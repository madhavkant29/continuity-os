# Security boundaries and deployment checklist

## Threat model

- Public clients must not call the FalkorDB graph or FastAPI directly. Only Next.js can attach the server-side API key.
- Only an authenticated operator can run or view simulations; all writes enforce same-origin checks. A review actor is read from the authenticated session, never request JSON.
- The company graph contains fictional personnel and authorization data. It is not a source of true privileges.
- An attacker could abuse a public sign-in route, so deploy behind a trusted reverse proxy with independent rate limiting and security alerts.
- A malicious or wrong input document may affect provenance records but cannot mint an access grant.
- A stolen session grants the authority of the configured single operator until expiration; rotate session secrets to invalidate all sessions.
- Caddy terminates TLS for the public demo. Never set `COOKIE_SECURE=false` for a publicly exposed host.

## Credentials

Run `python scripts/configure.py`. Do not check the generated `.env` into Git. Rotate the FastAPI key, FalkorDB password, operator password hash and session signing secret independently during a controlled deployment. Restart dependent services after rotation. Use a secret manager for a real deployment.

## Approval and reset safety

- Only explicit EXPIRED grants already present on the Person → Permission relationship can be renewed in the synthetic graph.
- A repair must still match the plan and record before application; the graph mutation uses an optimistic equality condition.
- Drills recalculate feasibility from FalkorDB. A failed new drill downgrades a previously verified repair.
- Reset is a fictional-data operation that deletes graph records; it requires an authenticated operator and a separate confirmation header.

## Remaining blockers for real organizational data

Identity provider, MFA, per-operation RBAC, separate review/approval actors, tenant isolation, real-data governance, data retention and privacy policies, robust backups and restoration tests, protected offsite audit trails, distributed rate limiting, security scans and runtime integration verification. None of these is optional for a commercially deployed enterprise product.

## Public judge mode

- Requires both `APP_MODE=demo` and `ENABLE_JUDGE_DEMO=true`; never enable on a real organization.
- One-click sign-in obtains a signed `demo` principal that cannot impersonate `operator` or choose a graph ID from browser parameters.
- A random graph namespace is minted server-side for every judge. Internal API service authentication remains mandatory. All guest mutations and resets use only that workspace.
- The server must enforce admission controls, rate limits, graph creation quotas, and stale guest graph cleanup at the infrastructure layer. The lightweight process-local throttle is insufficient protection for a high-traffic public endpoint.
- No real authorization or payment system is connected. Guests can approve fictional renewals only; the drill rechecks simulated feasibility.
