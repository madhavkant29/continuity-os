# Graph Hacks — Project brief and submission guide

## Overall challenge

Build a functional agent with FalkorDB as its essential context layer. The agent must reason about connected records, use those relationships to decide what to do, and explain the evidence paths behind its answers or actions. A decorative graph visualization does not satisfy the challenge.

## Track 3: Company Brain

Build an agent that understands how an organization operates across people, teams, projects, documents and decisions. Key expectations include shared organizational knowledge, ownership/expertise, provenance, updates to the graph, source-backed answers, and useful actions. See the [official challenge](https://www.wemakedevs.org/hackathons/falkordb) and [rules](https://www.wemakedevs.org/hackathons/falkordb/rules).

## ContinuityOS problem statement

Critical workflows may become impossible to execute when staff are unavailable, an essential permission is inactive, or separation-of-duty policies block every available assignment. Organizational information is fragmented, so managers can overlook these failure modes until work stops.

ContinuityOS uses FalkorDB to connect workforce capabilities, permissions, policies, document evidence and workflow dependencies. It simulates disruption, finds feasible assignments using a constraint solver, identifies blockers, proposes minimal policy-compliant remediation, records approvals, and verifies the revised scenario in a safe fictional environment.

### End-to-end judge scenario

1. Click **Explore live demo**; no signup or credentials are required.
2. Examine the seeded fictional company, its projects, decisions, and operational workflows.
3. Open **Company sources**; inspect original lines from a document, ticket and conversation.
4. Import a fictional ticket, review its association to the governing decision, and ask the analyst for a cited answer.
5. Simulate primary employee unavailability for a critical workflow; inspect graph-derived blockers.
6. Request a solver-generated repair, approve the fictional correction, and run the verification drill.
7. Inspect the graph and saved action trail. Reset the judge workspace if desired.

## Deployment

A public deployment is **preferred but not mandatory**. If the application cannot be deployed, the rules accept complete local setup instructions together with a working demo video. This project includes Docker Compose setup guidance and a one-click fictional judge mode for deployed use. Live deployment and complete browser/container verification must still be performed and documented.

## Submission checklist

- [ ] Public source repository, with truthful history and AI-assistance disclosure
- [ ] README with working setup steps and FalkorDB graph model
- [ ] Essential Cypher queries / graph algorithms explained and shown in use
- [ ] Working demo video showing real graph-backed behavior
- [ ] Live judge URL **or** complete, validated local setup instructions
- [ ] Track selection: Company Brain (plus other qualifying tracks, if entered)
- [ ] Only permitted public, synthetic or owned data
- [ ] Ability to explain core architecture, queries, solver and agent decisions
- [ ] Confirm organizer guidance about eligible development work

## Current engineering gaps

- Project nodes and document/ticket/conversation import are implemented in source with stable line-level citations, review states and revision tracking. Full Docker/browser integration has **not** been independently verified here.
- Source ingestion is a manual fictional-data importer, not automatic external Slack/Jira/Drive synchronization; reviewer association does not establish external truth.
- Public demo readiness requires actual HTTPS deployment, live smoke tests, distributed abuse protection and judge-namespace cleanup. See `DEPLOY_OPENCODE.md`.

## Metadata policy

Do not display project creation, edit, or update dates in the product UI, sample business records, reports, README, or release notes. Use monotonic sequence identifiers for fictional workflow/audit ordering. Preserve necessary security session expiration and original repository/deployment metadata rather than falsifying or rewriting evidence of authorship.
