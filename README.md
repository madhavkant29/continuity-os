# ContinuityOS

A FalkorDB-backed organizational continuity simulator with graph-grounded agent tools, constrained workforce assignment, sandbox recovery approvals, and replayable evidence. **Judges can use the one-click demo without creating an account.**

**Data classification:** This edition is a **single-organization, fictional-data sandbox**. It does not integrate with real identity providers, HR databases, payment systems, or production IAM. Do not put real personnel records, client contracts, or secrets into its document importer. Graph-backed simulation feasibility is not proof of real-world operational readiness.

## Scope

- Five fictional operational workflows; thirty employees and six departments. Each workflow has a linked Project, Decision and documented evidence.
- FalkorDB stores people, projects, required skills, grants, workflow steps, decisions, source-backed documents/tickets/conversations, passages, simulations, repairs and audit events.
- CP-SAT selects assignments subject to availability, skills, explicit active grants, and separation-of-duties constraints.
- When an existing grant is explicitly **EXPIRED**, the planner can propose a minimal sandbox renewal, which requires operator review and a subsequent verification drill. No missing grant is created automatically.
- The agent runs graph-grounded tools, retrieves exact quoted source lines with stable citation locators, and can persist an explicitly requested simulated continuity check. Optional LLM intent routing is disabled by default.
- **Company sources:** Import fictional documents, tickets and conversations; inspect original line citations; review their association to decisions; preserve edited revisions without hiding prior evidence.
- The app stores **no calendar fields or timestamps in its business graph, API payloads, screens, or audit records**. History uses monotonically increasing sequence numbers. Authorization uses short-lived cookies for security; no session metadata appears in business data.

## Start on a development machine

Prerequisites: Docker Engine and Docker Compose, and Python for one-time configuration.

```bash
python scripts/configure.py
# Enter an operator username and a strong password. The password is never stored in plaintext.
docker compose up --build -d
```

Open **http://localhost:3000**. Select **Explore live demo** to sign in immediately as **Demo Judge**, or use your configured operator credentials. Each demo session gets its own isolated, seeded FalkorDB graph and can reset its own scenario. No judge credentials or registration are necessary. The backend binds only to local loopback at `http://localhost:8000`, and the database is not published to the host. The frontend talks to FastAPI through a **same-origin server-side proxy**, which attaches the private backend credential; browser requests never receive the credential.

Live smoke verification resets synthetic records and should run only against an expendable demo graph:

```bash
python scripts/smoke.py
# Also test guest login and graph isolation through the frontend proxy:
python scripts/smoke_judge.py
```

Offline backend tests:

```bash
cd backend
python -m pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Frontend checks (requires registry access):

```bash
cd frontend
npm install
npm run lint
npm run build
```

### Safe resets

The in-app reset action requires a confirmation, and the backend requires a separate reset header. It **deletes all sandbox graph records**. Never reset a graph containing valued information. The application non-destructively upgrades the existing version-two demo graph to the version-three source/provenance schema. Back up before any migration; `docker compose down -v` is appropriate **only** for data you intend to erase.

## Secure public demo deployment

1. Point your DNS name at the host and allow incoming HTTPS and certificate validation traffic; restrict SSH and apply OS security patches.
2. Run `python scripts/configure.py` and set `PUBLIC_DOMAIN` in `.env` to your real hostname. Keep `.env` outside source control and readable only by the deployment operator.
3. Deploy with `docker compose -f docker-compose.yml -f docker-compose.public.yml up -d --build`.
4. Confirm automatic HTTPS is active, and ensure public access to the database and backend is disabled by your host firewall.
5. Confirm that **Explore live demo** appears on the login screen and creates a fresh fictional workspace without registration, while operator access still requires configured credentials. Confirm unauthenticated `/` redirects to `/login`, unauthorized API calls return 401, and no browser request contains a private backend token.
6. Run the smoke test only on a disposable instance; never run it against valued or real data.

The public overlay uses Caddy for TLS, secure session cookies, an explicitly configured trusted public origin, and HTTP hardening headers. Deploy it **only as a protected fictional-data demonstration**. Add ingress rate limits and WAF rules for public exposure; the in-process login throttle does not coordinate across replicas.

## Deployment protection

- **Operator login:** scrypt-stored password, signed short-lived HttpOnly session, SameSite=Strict cookies, and same-origin checks on modifications.
- **Judge demo:** One-click access is explicitly gated by `APP_MODE=demo` and `ENABLE_JUDGE_DEMO=true`. The demo role has a server-generated FalkorDB graph namespace in its signed session. Each visitor can simulate and approve *fictional sandbox* repairs, reset only their own graph, and cannot assume the operator role.
- **Service separation:** FastAPI denies requests lacking a private service token; FalkorDB uses a password and is never exposed directly. Backend access from localhost remains for smoke and diagnostics.
- **Least privilege:** Docker containers run unprivileged app users where supported; logs rotate; graph persists with AOF enabled.
- **Mutation safety:** No new permission grant is created. A recovery applies only if the observed expired grants still match the plan, using one atomic graph mutation and an optimistic repair-state check.
- **Reset boundary:** Demo-only and requires an explicit additional confirmation header. External LLM routing is disabled by default.
- **History:** Audit entries are sequentially ordered without time information. The system is not an immutable audit ledger or a regulated compliance system.

## Track 3 demonstration flow

Use **Explore live demo → Company sources** to inspect the existing document, ticket and conversation records. Paste a fictional ticket or process note, verify its association to the workflow decision and ask **Continuity Analyst** about it; returned source chips contain exact passages and clickable **Inspect original passage** links. Switch to the **Knowledge graph** to see Project/Decision/Source/Passage connections, then run **Disruption lab → Recovery queue → Verification drill**. Nothing touches real company infrastructure.

## Judge access

One-click demo is intentionally public **only for fictional data**. On first use, the server creates a new graph with five workflows and thirty synthetic people. The app presents all features without a signup or password; judges can run absence simulations, ask the agent to **Run and save an Ava Shah absence check**, propose repairs, approve sandbox-only permission renewals, run verification drills, and restart their own demo. Other judge sessions and the operator graph remain independent.

To disable judge access, set `ENABLE_JUDGE_DEMO=false` and restart the services. Do not enable judge access for a live organization. Each demo session creates a persistent graph; enable trusted-ingress rate limiting and operational quotas for public hosting, and delete stale guest graphs during maintenance. The included process-local limit is defense in depth, **not** sufficient protection against distributed abuse.

## Architectural notes

```text
Operator / judge ──HTTPS/local──> Next.js
                                   │ signed session
                                   │ same-origin API route
                                   ▼
                              FastAPI (private token)
                                   │
                                   ├── FalkorDB graph (authenticated + AOF)
                                   └── OR-Tools CP-SAT solver
```

Source of truth: FalkorDB relationship queries, not the model's guesses. API requests never fetch arbitrary external URLs. The optional LLM router only chooses from an allowlist; the agent can persist an explicitly requested synthetic continuity simulation. No real-world recovery action is automated.

For an exact deployment and live verification handoff, use **`DEPLOY_OPENCODE.md`**. See `docs/PROJECT_BRIEF_AND_SUBMISSION.md`, `docs/GRAPH_MODEL.md`, `docs/TEST_MATRIX.md`, `docs/DEMO_SCRIPT.md`, `docs/HACKATHON_COMPLIANCE.md`, and `NEXT_STEPS.md` for implementation details.

## Real production-readiness gaps

This package is **not a certified production SaaS**. Before using real organizations, implement OIDC/SAML and RBAC; true tenant isolation; external-source authenticity validation and automatic connector synchronization; database migration and encrypted offsite backups with tested restore; centralized auditing and monitoring; rate-limiting across replicas; security reviews; dependency pinning and vulnerability scans; and end-to-end Docker/browser integration tests. Until these are complete, keep the app limited to fictional test data and a controlled demonstration. There is no real permissions API integration and a passed drill only checks simulated assignment feasibility.

## Hackathon integrity

Check the latest organizer clarification regarding eligible development work. Retain truthful repository history, disclose AI assistance and reused code, and make sure meaningful engineering contributions are clearly demonstrable. A participant-reported community clarification may differ from the public rules; verify it with the organizers.
