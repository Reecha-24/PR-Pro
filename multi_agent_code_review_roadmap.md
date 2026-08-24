# Multi-Agent Code Review System — 6-Day Roadmap

> **Goal:** Build a working MVP that reviews real GitHub PRs end-to-end using 4 specialized AI agents and a synthesizer.

---

## Day 1: GitHub App & Webhook Infrastructure

**Goal:** The system can hear about PRs.

| Task | Details |
|------|---------|
| **Register GitHub App** | Create a GitHub App in your account. Give it `Pull requests` read/write, `Contents` read, `Issues` read. Note the App ID, private key, and webhook secret. |
| **Webhook receiver** | Build a `POST /webhooks/github` endpoint (NestJS/Go). Verify `X-Hub-Signature-256`. Parse `pull_request.opened` and `pull_request.synchronize`. |
| **Auth layer** | Implement GitHub App JWT + installation token exchange. You need this to call APIs on behalf of the installed repo. |
| **Smoke test** | Install the app on a test repo. Open a PR. Watch your server log the event payload. |

**End-of-day deliverable:** A running server that logs `PR #42 opened in repo X` every time you open or update a PR.

---

## Day 2: Diff Parsing & Job Orchestration

**Goal:** Fetch the PR content and queue it for review.

| Task | Details |
|------|---------|
| **Fetch diff** | Use GitHub's diff media type to grab the raw patch. Handle pagination for large PRs (>300 files). |
| **Diff parser** | Write a parser that turns the unified diff into structured objects: `file`, `hunk`, `line_number`, `change_type` (add/del/context). **Critical:** Calculate the `position` index for each hunk (GitHub's diff-position, not absolute line numbers). |
| **Redis + BullMQ (or Go queue)** | Set up Redis. On webhook receipt, enqueue a `review-pr` job with `{pr_id, repo, head_sha, files[]}`. |
| **Worker shell** | Create a worker that dequeues the job and logs "Processing PR #42". Don't add agents yet. |
| **DB setup** | PostgreSQL schema: `jobs`, `pr_reviews`, `suggestions`. |

**End-of-day deliverable:** Open a PR → your worker receives a structured array of changed files with correct diff positions.

---

## Day 3: The Agent Swarm (Parallel Execution)

**Goal:** 4 specialist agents run in parallel and return structured findings.

| Task | Details |
|------|---------|
| **OpenAI/Anthropic client** | Set up API client with function calling / structured output (Zod schema or JSON mode). |
| **Build 4 agents** | Create independent prompts/system roles: Security, Performance, Style, Logic. Each gets the diff + file list. |
| **Tool stubs** | Give agents 1–2 fake tools for now (e.g., Security Agent can "call" `npm audit` — just mock the response or run it if the repo has a `package.json`). Don't over-engineer tools on Day 3. |
| **Structured output enforcement** | Each agent must return JSON: `findings: [{file, line, position, severity, title, description, confidence}]`. If the LLM returns garbage, retry once. |
| **Parallel execution** | Use `Promise.all` (Node) or goroutines (Go) to fire all 4 agents simultaneously. Timeout: 60 seconds. |

**End-of-day deliverable:** Your worker can process a PR and print 4 JSON blobs of findings from the agents.

---

## Day 4: The Synthesizer & Comment Poster

**Goal:** Merge agent outputs into one coherent review and post it to GitHub.

| Task | Details |
|------|---------|
| **Synthesizer prompt** | Feed all 4 agent JSON outputs into a final LLM call. Prompt it to deduplicate, resolve conflicts, and output a final list of inline comments + a summary markdown body. |
| **Deduplication logic** | If two agents flag the same `file:position`, merge them into one comment with both labels. |
| **Confidence filter** | Drop anything with `< 0.7` confidence unless severity is `critical`. |
| **GitHub Review API** | POST to `/repos/{owner}/{repo}/pulls/{number}/reviews`. Use `event: "COMMENT"`. Attach inline comments using the `position` you calculated on Day 2. Post summary as `body`. |
| **Error handling** | Handle invalid positions (GitHub will reject). Log and skip that specific comment, don't fail the whole review. |

**End-of-day deliverable:** Open a PR in your test repo. The bot posts a single review comment with inline suggestions and a summary. This is your **MVP moment**.

---

## Day 5: Database, Learning Layer & Feedback Loop

**Goal:** Persist reviews and start tracking what works.

| Task | Details |
|------|---------|
| **Persist suggestions** | Every finding from every agent gets saved to the `suggestions` table before posting. |
| **Resolution tracker** | Poll GitHub or use webhook `pull_request_review_comment` events to detect when a comment is marked "Resolved" by a human. Update `was_accepted = true`. |
| **Rejection tracking** | If a comment is deleted or the PR is merged without the suggestion being applied, mark `was_accepted = false`. (Heuristic-based is fine for MVP.) |
| **Agent performance view** | Query: `SELECT agent, AVG(confidence), SUM(CASE WHEN was_accepted THEN 1 ELSE 0 END) / COUNT(*) as accuracy FROM suggestions GROUP BY agent`. |
| **Prompt refinement** | Use the data to tweak one agent prompt. E.g., if Security Agent has 20% acceptance, add "Only flag issues where a secret is actually hardcoded, not just referenced." |

**End-of-day deliverable:** A dashboard query (or simple CLI printout) showing each agent's accuracy rate. You can see which agent is helpful and which is noisy.

---

## Day 6: Testing, Hardening & Deployment

**Goal:** The system is robust enough to leave running on a real repo.

| Task | Details |
|------|---------|
| **Rate limiting** | Add GitHub API rate limit checks. If remaining requests < 100, pause queue. |
| **Large PR handling** | If PR > 50 files or > 5000 lines, skip non-critical files or summarize instead of line-by-line review. |
| **Retry & dead-letter** | If an agent times out or LLM API fails, retry twice then move job to a dead-letter queue for manual inspection. |
| **Dockerize** | `Dockerfile` for your server + `docker-compose.yml` with Redis and Postgres. |
| **Deploy** | Push to Render/Railway/Fly.io. Set up a persistent tunnel/webhook URL. Install the GitHub App on a real side-project repo. |
| **Final demo** | Open a real PR with a known bug (e.g., `eval(userInput)`). Watch Security Agent catch it, Synthesizer merge it, and the comment appear. |

**End-of-day deliverable:** A live URL, a running GitHub App on a real repository, and a PR that was reviewed by your agent swarm.

---

## Daily Time Split (Recommended)

| Component | Time |
|-----------|------|
| Backend/API/DB work | ~60% |
| Prompt engineering / Agent logic | ~30% |
| Testing with real PRs | ~10% |

---

## Recovery Plan (If You Fall Behind)

| Behind on... | Recovery Action |
|--------------|-----------------|
| **Day 3** | Start with 2 agents (Security + Logic) instead of 4. Add Style and Performance later. |
| **Day 4** | Skip the Synthesizer. Post each agent's findings as separate reviews. Build the Synthesizer on Day 5. |
| **Day 5** | The learning layer is a "nice to have." The MVP is done on Day 4. Treat Day 5–6 as polish. |

---

## Tech Stack

- **Runtime:** Node.js / NestJS (or Go)
- **Queue:** Redis + BullMQ
- **Database:** PostgreSQL
- **LLM:** OpenAI GPT-4o / Anthropic Claude
- **GitHub API:** GitHub Apps API (REST)
- **Deployment:** Docker + Render / Railway / Fly.io

---

*Generated for intermediate backend + agentic AI project building.*
