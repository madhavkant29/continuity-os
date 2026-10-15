# FalkorDB graph model and source provenance

FalkorDB is the authoritative graph for the **fictional Northstar Payments demonstration**. There is no live HR, IAM, payment, ticket, or messaging integration. Data is scoped to an authenticated operator graph or an isolated judge graph.

## Organizational nodes

```cypher
(:Person)-[:MEMBER_OF]->(:Team)
(:Person)-[:HAS_SKILL]->(:Skill)
(:Person)-[:GRANTED {state:'ACTIVE'|'EXPIRED'|'REVOKED'}]->(:Permission)
(:Team)-[:OWNS]->(:Workflow)
(:Team)-[:OWNS]->(:Project)
(:Project)-[:DELIVERS]->(:Workflow)
(:Workflow)-[:HAS_STEP]->(:Step)
(:Step)-[:REQUIRES_SKILL]->(:Skill)
(:Step)-[:REQUIRES_PERMISSION]->(:Permission)
(:Step)-[:SEPARATE_FROM]->(:Step)
(:Step)-[:PRECEDES]->(:Step)
(:Decision)-[:GOVERNS]->(:Workflow)
```

## Source and review nodes

```cypher
(:Source {kind:'DOCUMENT'|'TICKET'|'CONVERSATION'})-[:ABOUT]->(:Workflow)
(:Source)-[:IN_PROJECT]->(:Project)
(:Source)-[:MENTIONS]->(:Decision)
(:Passage)-[:EXCERPT_OF]->(:Source)
(:Passage)-[:CITED_IN_REVIEW]->(:Decision)
(:Source)-[:REVISION_OF]->(:Source)
```

Source records contain original pasted text, a SHA-256 content fingerprint, an optional external reference, a current-version flag and a review status. Passage records contain **the verbatim source line**, its one-based original line number, and an unambiguous locator such as `src:<stable-hash>#L3`.

Each of the five seeded projects includes a fictional document, ticket and conversation. The seeded sources carry `SYNTHETIC_VERIFIED` status to distinguish them from manually imported evidence. Manual evidence starts as `PENDING_REVIEW` and is never automatically elevated to a verified policy. An authenticated reviewer can confirm its relationship to the associated workflow and decision, producing a `CITED_IN_REVIEW` edge. That *reviewed association is not a legal determination or validation of the truth of every sentence*.

Edits using an identical workflow, source type and external reference produce a new source node while keeping the older version accessible via `REVISION_OF`. Exact repeat imports are idempotent. Superseded sources are excluded from current evidence search.

## Exact citation traversal

```cypher
MATCH (p:Passage)-[:EXCERPT_OF]->(s:Source {current:true})
      -[:ABOUT]->(w:Workflow {id:$wid})
RETURN p.id, p.locator, p.quote, s.id, s.kind,
       s.title, s.reference, s.review_status
ORDER BY s.kind, p.line
```

The deterministic analyst retrieves passage text from FalkorDB and selects passages with literal keyword overlap. It quotes stored text and returns the source ID, passage ID, exact locator, and verification status. No AI-generated quotations or invented URLs are used. Search may produce **no matched evidence**; the agent must then decline to infer an unsupported answer. It is *not* a general-purpose semantic RAG system.

## Runtime and audit entities

```cypher
(:Simulation)-[:TESTS]->(:Workflow)
(:Repair)-[:ADDRESSES]->(:Simulation)
(:Drill)-[:VERIFIES]->(:Repair)
(:AgentRun)-[:CONTEXT_FOR]->(:Workflow)
(:AuditEvent {sequence: 1})
```

The solver loads eligibility facts from the graph, enforces skills, active grants and separation of duties, and returns a feasible assignment or a blocked result. Repairs can renew **only existing expired fictional grants** after approval. A sandbox verification reruns feasibility; it does not perform a real business transaction.

The graph has a non-destructive upgrade path from schema version 2 to 3. Legacy `Document` nodes remain available for compatibility, while new evidence features use `Source` and `Passage`. Back up the named volume before any migration.

No creation or modification dates are stored in application business records. Ordering of audit and simulation activity uses sequence numbers.
