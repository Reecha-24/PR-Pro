from typing import Any, Dict, List, Tuple
from collections import defaultdict

# Numeric mapping for confidence string/enum values
CONFIDENCE_MAP = {
    "high": 0.9,
    "medium": 0.7,
    "low": 0.4,
}


def get_enum_val(val: Any) -> str:
    """Safely extracts lowercase string value from an Enum or string."""
    if hasattr(val, "value"):
        return str(val.value).lower()
    return str(val).lower() if val is not None else ""


def filter_findings(findings: List[Any]) -> List[Any]:
    """
    Confidence filter: Drop anything with confidence < 0.7
    UNLESS severity is CRITICAL or HIGH.
    """
    if not findings:
        return []

    valid = []
    for f in findings:
        # Ignore malformed diff header artifacts
        if getattr(f, "file", None) and f.file.startswith("{filename}"):
            continue

        conf_str = get_enum_val(f.confidence)
        conf_val = CONFIDENCE_MAP.get(conf_str, 0.5)
        sev_str = get_enum_val(f.severity)

        # Include if confidence is high enough OR severity is critical/high
        if conf_val >= 0.7 or sev_str in ["critical", "high"]:
            valid.append(f)

    return valid


def synthesize_results(results_input: Any) -> Tuple[List[Dict[str, Any]], str]:
    """
    Synthesizes findings from a PRReviewResponse object or dictionary
    into inline comments and a summary Markdown body.
    """
    agent_names = ["security", "performance", "style", "logic"]
    
    # Extract agent results without using .items() on Pydantic models
    agent_items = []
    if isinstance(results_input, dict):
        for name in agent_names:
            if name in results_input and results_input[name]:
                agent_items.append((name, results_input[name]))
    else:
        for name in agent_names:
            agent_res = getattr(results_input, name, None)
            if agent_res:
                agent_items.append((name, agent_res))

    grouped_inline: Dict[Tuple[str, int], List[Tuple[str, Any]]] = defaultdict(list)
    general_findings: List[Tuple[str, Any]] = []
    total_valid_findings = 0
    agent_filtered_counts: Dict[str, int] = {}

    # 1. Process agent findings through the updated filter_findings function
    for agent_name, agent_result in agent_items:
        raw_findings = getattr(agent_result, "findings", None) or []
        
        filtered = filter_findings(raw_findings)
        
        agent_filtered_counts[agent_name] = len(filtered)
        total_valid_findings += len(filtered)

        for f in filtered:
            target_pos = f.position if f.position is not None else f.line

            if target_pos is not None and f.file:
                grouped_inline[(f.file, target_pos)].append((agent_name, f))
            else:
                general_findings.append((agent_name, f))

    # 2. Build inline comments
    inline_comments = []
    for (file_path, pos), items in grouped_inline.items():
        body_parts = []
        for agent_name, f in items:
            sev_upper = get_enum_val(f.severity).upper()
            part = f"### ⚠️ [{agent_name.upper()}] {f.title} (`{sev_upper}`)\n{f.description}"
            if getattr(f, "suggestion", None):
                part += f"\n\n**💡 Suggestion:**\n{f.suggestion}"
            body_parts.append(part)

        merged_body = "\n\n---\n\n".join(body_parts)
        inline_comments.append({
            "path": file_path,
            "body": merged_body,
            "position": pos
        })

    # 3. Build summary body markdown
    summary = "## 🤖 AI Code Review Summary\n\n"
    summary += f"- **Total Actionable Findings:** {total_valid_findings}\n\n"
    summary += "### 📊 Agent Breakdown\n"

    emoji_map = {
        "security": "🔒",
        "performance": "⚡",
        "style": "🎨",
        "logic": "🧠"
    }

    for agent_name, _ in agent_items:
        count = agent_filtered_counts.get(agent_name, 0)
        emoji = emoji_map.get(agent_name, "🔍")
        summary += f"- **{emoji} {agent_name.capitalize()} Agent:** {count} finding(s)\n"

    if general_findings:
        summary += "\n### 📌 Repository & Dependency Warnings\n"
        for agent_name, f in general_findings:
            sev_upper = get_enum_val(f.severity).upper()
            file_label = f"`{f.file}`" if f.file else "Repository"
            summary += f"- **[{agent_name.upper()}] [{sev_upper}] {file_label}:** {f.title}\n  _{f.description}_\n"

    summary += "\n---\n*Review generated automatically by Multi-Agent PR Reviewer.*"

    return inline_comments, summary