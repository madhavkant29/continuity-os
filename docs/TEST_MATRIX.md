# Test matrix

| Check | Automated entry point | Validation |
|---|---|---|
| Solver eligibility and separation constraints | `backend/tests/test_solver.py` | Deterministic unit tests |
| Authentication, demo scoping and reviewer identity | `backend/tests/test_security.py` | FastAPI negative tests with mocked storage |
| Analyst source grounding and explicit persistence | `backend/tests/test_agent.py`, `backend/tests/test_knowledge.py` | Unit tests |
| Stable original line citation | `backend/tests/test_knowledge.py` | One-based source lines, including gaps |
| Import idempotency and source versioning | `backend/tests/test_knowledge.py` | Key and hash tests |
| Manual imports cannot self-verify | `backend/tests/test_knowledge.py` | Writes never create review support edges |
| FalkorDB persistence, solver, repair and drill | `python scripts/smoke.py` | **Requires actual Docker stack** |
| Two judge sessions, source import/review, cited answers, graph, isolation | `python scripts/smoke_judge.py` | **Requires actual frontend and database** |
| Session token integrity | `cd frontend && npm run test` | Local Node tests |
| Production TypeScript and Next build | `cd frontend && npm run lint && npm run build` | **Requires npm dependencies** |
| External HTTPS, origin checks, secrets, network isolation | `DEPLOY_OPENCODE.md` | **Requires a public deployment** |

A passing offline unit test does not establish that FalkorDB Cypher queries, Docker health checks, browsers, or live TLS actually work. These are explicit deployment gates.
