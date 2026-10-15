# Verification status

This file now records checks that were **actually executed**, including the public HTTPS deployment. Everything below has command output or captured evidence backing it. The previous, offline-only status is superseded.

## Public deployment

- **HTTPS URL:** `https://13-127-48-212.sslip.io` (dedicated single host, synthetic data only).
- Let's Encrypt certificate issued and trusted (chain verified programmatically); HTTP 308-redirects to HTTPS.
- Security headers active (HSTS, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`).
- External port scan: only 80/443 are public; backend (8000) and FalkorDB (6379) are unreachable externally and bound to loopback/private network. SSH is restricted to the administrator's IP.
- Edge rate limits enforced by Caddy (official `caddy-ratelimit` plugin); burst test returned HTTP 429. `X-Real-IP` is forwarded so per-IP app throttles work behind the proxy.

## Backend

- Unit tests: **30 passed** (`PYTHONPATH=backend pytest -q`), including solver, agent, auth boundary, guest scopes, citations, revision identity, guest-workspace cap, and cleanup-tool guards.
- `pip-audit -r backend/requirements.txt`: **no known vulnerabilities**.
- Live operator smoke (`scripts/smoke.py`) against a real FalkorDB stack: **PASS** locally and on the deployed host — graph persistence, constraint solving, proposal, sandbox approval, drill, agent answers, audit.
- FalkorDB data survived a container restart on the deployed host (30 employees, 5 workflows, audit events intact).

## Frontend

- Session tests: **5 passed**; `tsc --noEmit` clean; `next build` compiles (Next.js 15.5.28, sharp 0.35.5).
- npm audit: 0 critical, 0 high runtime advisories after upgrades. Residual: 2 moderate/high **build-time** postcss advisories inherited from Next 15 tooling, with no user-controlled CSS input in this application; a fix requires the Next 16 major upgrade.

## Judge experience (real Chromium engine, headless)

- One-click **Explore live demo** opens the Northstar Payments dashboard with no signup.
- Featured scenario: **BLOCKED** simulation → policy-safe repair proposal → sandbox approval → drill **VERIFIED**.
- Ticket import shows `PENDING_REVIEW`; reviewer confirmation marks it `VERIFIED`; exact `#L1` line-locator citation rendered.
- Knowledge graph rendered with passage/document/decision/project/workflow/step/skill/permission/person nodes (30 nodes, 41 relations for the refund workflow).
- Two parallel judge sessions are isolated (separate graphs; no cross-visibility of sources or repairs).
- No private service key appeared in any browser request; zero uncaught page errors during the walkthrough.
- `scripts/smoke_judge.py` **PASS** against the public HTTPS origin (login, ingestion, review, citations, graph, simulation, isolation, reset).

## Public-hosting safeguards

- Bounded guest workspaces (`MAX_DEMO_GRAPHS`): verified HTTP 503 once the cap is reached.
- Maintenance tooling verified live: `python -m app.maintenance list|delete-all` removed abandoned judge graphs; only guest namespaces are touchable.
- Container resource limits applied (verified via container inspection); bounded json-file logs on every service.
- CloudWatch billing alarm (30 USD) and EC2 status-check alarm created; an operator must confirm the SNS email subscription to receive pages.

## Known limitations (honest boundaries)

- Browser verification used headless Edge/Chromium; manual mobile-layout and keyboard-navigation checks were not visually reviewed.
- Session-expiration UI behavior and the in-app reset confirmation were validated at the API/throttle level, not by waiting out a real 8-hour cookie.
- No WAF, no offsite backup, no HA; single small instance with AOF persistence only.
- The sandbox drill proves simulated assignment feasibility, not real-world recovery. No real systems are connected.

Verification executed by OpenCode (AI) under operator instruction; command outputs are retained in the deployment session record.
