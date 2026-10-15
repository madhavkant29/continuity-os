# Track 3 compliance and limitations

Official reference: https://www.wemakedevs.org/hackathons/falkordb

This is a technical self-assessment, **not a ruling by the organizer**.

| Track 3 capability | Implementation | Honest boundary |
|---|---|---|
| FalkorDB as central context graph | Graph stores people, teams, projects, workflows, grants, decisions, passages, simulations, approvals and audits | Must run live graph smoke before final submission |
| Know who owns what and who knows what | Team ownership, skills, grants and task eligibility with constraint solving | Fictional company only |
| Ingest documents, tickets and conversations | Three first-class source types; seeded records and manual text import API/UI | No automatic Slack, Jira or Drive sync; imports are user-provided text |
| Trace decisions to evidence | Sources link to decisions, passages have exact locators, original quotes and review status | Reviewed association does not prove that a sentence is true |
| Knowledge changes | Idempotent import, revision links, current/superseded distinction, review state, persistent graph | No continuous external synchronization |
| Graph-grounded agent responses | Literal source passage retrieval and explicit evidence labels | Keyword matching only; a query can lack matches |
| Useful agent actions | Explicitly requested checks are saved to FalkorDB; the UI creates and approves sandbox repair proposals | No real permissions or payments modified |
| Judge access | One-click fictional demo with isolated graph namespaces | Public abuse controls and guest graph cleanup need hosting safeguards |
| Full deployment verification | Local containers and HTTPS proxy are configured; two smoke scripts provided | Must be executed by OpenCode in an environment with Docker and hosting access |
| Submission format | Public repo, demo explanation and setup steps documented | Check current organizer portal and clarify any development eligibility questions |

Use `docs/DEMO_SCRIPT.md`, `docs/GRAPH_MODEL.md`, `scripts/smoke.py`, and `scripts/smoke_judge.py` to show the actual graph path rather than claiming novelty based only on the interface.

Keep repository history accurate and disclose AI-assisted work and reused code where required. If the organizer clarified the permissible build window in Discord, retain the official clarification and follow it.
