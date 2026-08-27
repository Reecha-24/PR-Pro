import random
from typing import Dict, Any

async def mock_npm_audit(package_json_content: str) -> Dict[str, Any]:
    """Fake npm audit - returns mock vulnerabilities"""
    return {
        "vulnerabilities": [
            {
                "package": "lodash",
                "severity": "moderate",
                "title": "Prototype Pollution",
                "version": "<4.17.21"
            }
        ],
        "metadata": {
            "vulnerabilities": {"info": 0, "low": 0, "moderate": 1, "high": 0, "critical": 0}
        }
    }

async def mock_complexity_analyzer(code_snippet: str) -> Dict[str, Any]:
    """Fake cyclomatic complexity checker"""
    return {
        "complexity_score": random.randint(3, 15),
        "recommendation": "Consider breaking into smaller functions" if random.random() > 0.5 else "Complexity is acceptable"
    }

async def mock_linter_check(file_path: str, code: str) -> Dict[str, Any]:
    """Fake linter - returns style issues"""
    issues = []
    if "var " in code:
        issues.append({"rule": "no-var", "message": "Use 'const' or 'let' instead of 'var'"})
    if len(code) > 500 and "\n" in code:
        issues.append({"rule": "max-lines-per-function", "message": "Function exceeds 50 lines"})
    return {"issues": issues, "passed": len(issues) == 0}

async def mock_type_checker(code: str) -> Dict[str, Any]:
    """Fake type checker"""
    return {
        "type_errors": [],
        "warnings": ["Consider adding type hints"] if "def " in code and "->" not in code else []
    }