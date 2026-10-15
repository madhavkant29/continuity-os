# OpenCode — final integration and deployment tasks

Start with `DEPLOY_OPENCODE.md` and execute it **in order**. You are maintaining an existing Next.js + FastAPI + FalkorDB + OR-Tools application; do not replace its graph-centered architecture or redesign the whole product.

## Priorities

1. **Run and fix real integrations.** Install dependencies; run the backend unit suite and frontend tests, TypeScript and production build. Start Docker Compose with a real FalkorDB instance. Fix any Cypher/API/frontend issues exposed by the actual stack. Exercise both smoke scripts until they pass without changing assertions.
2. **Finish source-backed Track 3 acceptance.** Verify the Company Sources UI imports documents, tickets and conversations; imported records start pending review; reviews are authenticated; passage citations resolve to exact stored lines; duplicate imports are idempotent; updated reference content preserves previous revisions; and Project/Decision/Source/Passage edges appear in the knowledge graph.
3. **Deploy the judge demo.** Follow `DEPLOY_OPENCODE.md` for DNS, TLS and Docker deployment. Set demo and cookie security configuration. Perform a browser-level walkthrough of one-click login, source import/review/agent citations, interruption simulation, repair and sandbox drill. Verify two simultaneous judge sessions cannot read or reset each other's graph.
4. **Public-hosting safeguards.** Add ingress rate limits, resource quotas and a cleanup process for abandoned guest graphs; verify firewall and container credentials; protect the Caddy and application endpoints against abuse. Do not ingest real company data or connect real financial systems.
5. **Presentation and handoff.** Update `VERIFICATION.md` with checks actually run (no fabricated passes). Capture screenshots and a concise demo video. Update the README and official submission checklist, commit lockfiles and disclose AI assistance where needed.

## Non-negotiable constraints

- Keep the app's business records and visible interface free of creation/modification timestamps and calendar dates. Session security mechanisms and unavoidable infrastructure metadata must remain functional; do not forge repository history.
- All authorization decisions must be derived from FalkorDB's recorded skills/grants and a deterministic constraint solver. A free-form LLM cannot fabricate a permission, source quote or decision.
- Manually imported sources are `PENDING_REVIEW` until an authorized reviewer confirms their association. Review does not independently verify every factual claim. Preserve exact line-level citations and superseded revisions.
- No real personnel, client, financial, access-control or production IAM data may enter the public demo. Sandbox operations must remain fictional and explicitly labeled as such.
- Do not declare the app deployed or production-ready unless real integration, browser and security checks support that claim. Report unresolved blockers.

The full deployment commands and acceptance checklist are in **`DEPLOY_OPENCODE.md`**.
