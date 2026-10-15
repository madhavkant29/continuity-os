"""FalkorDB is the system of record. No production in-memory fallback.

All graph reads used by the planner come from these relationship queries.
Graph write operations intentionally target a seeded sandbox organization only.
"""
from __future__ import annotations

import json
import hashlib
import os
import uuid
from typing import Any

from .sample import PERMISSIONS, ROSTER, SKILLS, TEAMS, WORKFLOWS
from .solver import analyze, solve
from .knowledge import passages, source_identity, rank_passages, KINDS



def encode(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


class GraphStore:
    def __init__(self, graph_name: str | None = None):
        from falkordb import FalkorDB
        self.client = FalkorDB(host=os.getenv("FALKOR_HOST", "localhost"),
                               port=int(os.getenv("FALKOR_PORT", "6379")),
                               password=os.getenv("FALKOR_PASSWORD") or None,
                               socket_connect_timeout=5)
        self.graph_name = graph_name or os.getenv("FALKOR_GRAPH", "continuity_demo")
        self.graph = self.client.select_graph(self.graph_name)

    def read(self, cypher: str, params: dict | None = None) -> list[list]:
        return self.graph.ro_query(cypher, params or {}).result_set

    def write(self, cypher: str, params: dict | None = None) -> list[list]:
        return self.graph.query(cypher, params or {}).result_set

    def ensure_seeded(self):
        # Write-query creates an empty graph on first boot; read-only queries may
        # otherwise fail with "graph does not exist" before the first seed.
        self.write("MERGE (:Bootstrap {id:'bootstrap'})")
        rows = self.read("MATCH (w:Workflow) RETURN count(w)")
        if not rows or rows[0][0] == 0:
            # The bootstrap marker is the only permitted existing record before first seed.
            existing=self.read("MATCH (n) RETURN count(n)")[0][0]
            if existing != 1 or os.getenv("APP_MODE", "demo") != "demo":
                raise RuntimeError("Graph is not a fresh demo datastore; refusing automatic destructive seed")
            self.seed_demo()
        elif self.read("MATCH (s:Schema {id:'main',version:2}) RETURN s.id"):
            # Non-destructive upgrade of existing version-two graphs. Legacy
            # title-only Document nodes remain intact for audit compatibility.
            self.seed_knowledge_pack()
            self.write("MATCH (s:Schema {id:'main'}) SET s.version=3")
        elif not self.read("MATCH (s:Schema {id:'main',version:3}) RETURN s.id"):
            raise RuntimeError("Unsupported graph schema; backup and migrate existing data")

    def seed_demo(self):
        if os.getenv("APP_MODE", "demo") != "demo":
            raise PermissionError("Seeding is only allowed in APP_MODE=demo")
        # Developer-only reset. Never expose this endpoint on a public production instance.
        self.write("MATCH (n) DETACH DELETE n")
        self.write("CREATE (:Schema {id:'main',version:3})")
        self.write("UNWIND $xs AS x MERGE (t:Team {id:x}) SET t.name=x", {"xs": TEAMS})
        self.write("UNWIND $xs AS x MERGE (s:Skill {id:x}) SET s.name=x", {"xs": SKILLS})
        self.write("UNWIND $xs AS x MERGE (p:Permission {id:x}) SET p.name=x", {"xs": PERMISSIONS})
        people = [{"id":pid,"name":name,"team":team,"role":role,"active":True}
                  for pid,name,team,role,*_ in ROSTER]
        self.write("""UNWIND $xs AS x MERGE (p:Person {id:x.id})
                     SET p.name=x.name, p.role=x.role, p.active=x.active
                     WITH p,x MATCH (t:Team {id:x.team}) MERGE (p)-[:MEMBER_OF]->(t)""", {"xs":people})
        skills = [{"id":pid,"skill":skill} for pid,_,_,_,known,_,_ in ROSTER for skill in known]
        self.write("""UNWIND $xs AS x MATCH (p:Person {id:x.id}), (s:Skill {id:x.skill})
                     MERGE (p)-[:HAS_SKILL]->(s)""", {"xs":skills})
        grants = [{"id":pid,"perm":perm,"state":"EXPIRED" if perm in expired else "ACTIVE"}
                  for pid,_,_,_,_,allowed,expired in ROSTER for perm in allowed]
        self.write("""UNWIND $xs AS x MATCH (p:Person {id:x.id}), (perm:Permission {id:x.perm})
                     MERGE (p)-[r:GRANTED]->(perm) SET r.state=x.state, r.source='seeded-access-registry'""", {"xs":grants})
        workflows = [{"id":w["id"],"name":w["name"],"department":w["department"],
                      "criticality":w["criticality"],"description":w["description"],"owner":w["owner"]} for w in WORKFLOWS]
        self.write("""UNWIND $xs AS x MERGE (w:Workflow {id:x.id})
                     SET w.name=x.name,w.department=x.department,w.criticality=x.criticality,w.description=x.description
                     WITH w,x MATCH (t:Team {id:x.owner}) MERGE (t)-[:OWNS]->(w)""", {"xs":workflows})
        steps = [{"id":w["id"]+":"+sid,"workflow":w["id"],"short_id":sid,"name":name,
                  "position":i+1,"skill":skill,"permission":perm}
                 for w in WORKFLOWS for i,(sid,name,skill,perm) in enumerate(w["steps"])]
        self.write("""UNWIND $xs AS x MATCH (w:Workflow {id:x.workflow}),
                     (skill:Skill {id:x.skill}),(perm:Permission {id:x.permission})
                     MERGE (s:Step {id:x.id}) SET s.short_id=x.short_id,s.name=x.name,s.position=x.position
                     MERGE (w)-[:HAS_STEP]->(s)
                     MERGE (s)-[:REQUIRES_SKILL]->(skill)
                     MERGE (s)-[:REQUIRES_PERMISSION]->(perm)""", {"xs":steps})
        edges = [{"a":w["id"]+":"+a,"b":w["id"]+":"+b} for w in WORKFLOWS for a,b in w["separation"]]
        self.write("""UNWIND $xs AS x MATCH (a:Step {id:x.a}), (b:Step {id:x.b})
                     MERGE (a)-[:SEPARATE_FROM]->(b)""", {"xs":edges})
        before = [{"a":w["id"]+":"+w["steps"][i][0], "b":w["id"]+":"+w["steps"][i+1][0]}
                  for w in WORKFLOWS for i in range(len(w["steps"])-1)]
        self.write("""UNWIND $xs AS x MATCH (a:Step {id:x.a}),(b:Step {id:x.b})
                     MERGE (a)-[:PRECEDES]->(b)""", {"xs":before})
        docrows=[{"id":f"doc:{w['id']}:{i}","title":title,"workflow":w["id"],"source":"Synthetic operating manual", "version":"1"}
                 for w in WORKFLOWS for i,title in enumerate(w["docs"])]
        self.write("""UNWIND $xs AS x MATCH (w:Workflow {id:x.workflow})
                     MERGE (d:Document {id:x.id}) SET d.title=x.title,d.source=x.source,d.version=x.version
                     MERGE (d)-[:DESCRIBES]->(w)""", {"xs":docrows})
        decisions=[{"id":"decision:"+w["id"],"name":w["decision"],"workflow":w["id"]} for w in WORKFLOWS]
        self.write("""UNWIND $xs AS x MATCH (w:Workflow {id:x.workflow})
                     MERGE (d:Decision {id:x.id}) SET d.title=x.name,d.source='synthetic-governance-record'
                     MERGE (d)-[:GOVERNS]->(w)""", {"xs":decisions})
        self.seed_knowledge_pack()
        self.record_event("DATASET_SEEDED", "Seeded 30 fictional employees and five workflows", "system", "dataset")
        return {"workflows":len(WORKFLOWS), "employees":len(ROSTER), "workspace":"synthetic"}

    def seed_knowledge_pack(self):
        """Create cited, fictional documents, tickets, conversations and projects.

        Every line is actual source content in FalkorDB, not just a document title.
        Re-running this routine is idempotent and never alters imported records.
        """
        for flow in WORKFLOWS:
            wid=flow["id"]
            pid="project:"+wid
            self.write("""MATCH (w:Workflow {id:$wid})
                MERGE (p:Project {id:$pid}) SET p.name=$name, p.state='ACTIVE'
                MERGE (p)-[:DELIVERS]->(w)
                WITH p MATCH (t:Team {id:$team}) MERGE (t)-[:OWNS]->(p)""",
                {"wid":wid,"pid":pid,"name":flow["name"]+" continuity","team":flow["owner"]})
            decision="decision:"+wid
            seeds=[
                ("DOCUMENT",flow["docs"][0],"MANUAL-"+wid,
                 f"Scope: {flow['name']}.\nRequired procedure: {flow['description']}\nControl decision: {flow['decision']}.\nProcess owner: {flow['owner']} team."),
                ("TICKET","Readiness verification ticket","TASK-"+wid,
                 f"Work item: verify operational continuity for {flow['name']}.\nOwner: {flow['owner']} team.\nAcceptance: validate independent execution and currently active grants.\nDecision to validate: {flow['decision']}."),
                ("CONVERSATION","Operational handoff discussion","CHAT-"+wid,
                 f"{flow['owner']} lead: Who can cover the {flow['name']} workflow when the primary operator is unavailable?\nRisk reviewer: Confirm both the required skills and active permissions, not job title alone.\n{flow['owner']} lead: Keep {flow['decision'].lower()} and run a sandbox verification before closure.")
            ]
            for kind,title,ref,content in seeds:
                ident,key,digest=source_identity(wid,kind,title,ref,content)
                self._write_source(wid,ident,key,digest,kind,title,ref,content,
                                   "SYNTHETIC_VERIFIED",decision,pid)

    def _write_source(self, wid, identifier, key, digest, kind, title, ref, content,
                      status, decision_id, project_id):
        self.write("""MATCH (w:Workflow {id:$wid}),(d:Decision {id:$decision}),
                           (project:Project {id:$project})
            MERGE (s:Source {id:$id})
            SET s.source_key=$key,s.content_hash=$digest,s.kind=$kind,
                s.title=$title,s.reference=$ref,s.content=$content,
                s.review_status=$status,s.current=true
            MERGE (s)-[:ABOUT]->(w)
            MERGE (s)-[:IN_PROJECT]->(project)
            MERGE (s)-[:MENTIONS]->(d)""",
            {"wid":wid,"decision":decision_id,"project":project_id,
             "id":identifier,"key":key,"digest":digest,"kind":kind,
             "title":title,"ref":ref,"content":content,"status":status})
        lines=passages(content,identifier)
        self.write("""UNWIND $rows AS x MATCH (s:Source {id:$id})
            MERGE (p:Passage {id:x.id})
            SET p.locator=x.locator,p.line=x.line,p.quote=x.quote
            MERGE (p)-[:EXCERPT_OF]->(s)""",{"id":identifier,"rows":lines})
        if status in ("VERIFIED", "SYNTHETIC_VERIFIED"):
            self.write("""MATCH (s:Source {id:$id})-[:MENTIONS]->(d:Decision)
                MATCH (p:Passage)-[:EXCERPT_OF]->(s)
                MERGE (p)-[:CITED_IN_REVIEW]->(d)""",{"id":identifier})
        return lines

    def ingest_source(self, wid: str, kind: str, title: str, content: str,
                      reference: str = "") -> dict:
        """Manual import is unverified until reviewed by an authenticated operator.

        Update by identical kind+reference (or title), keeping older versions.
        No automatic claim verification or outside integrations are asserted.
        """
        self.snapshot(wid)
        if kind not in KINDS or not 3 <= len(title.strip()) <= 160 or not 10 <= len(content) <= 10000:
            raise ValueError("Invalid source type, title, or content length")
        if len(reference)>120 or len(content.splitlines())>120:
            raise ValueError("Source reference or line count exceeds the limit")
        ident,key,digest=source_identity(wid,kind,title,reference,content)
        existing=self.read("MATCH (s:Source {id:$id}) RETURN s.id",{"id":ident})
        if existing:
            return self.get_source(ident)
        # Cap retained versions as well as current sources in public judge graphs.
        # Distributed request limits and guest namespace cleanup are additional host controls.
        count=self.read("MATCH (s:Source) RETURN count(s)")
        if count and count[0][0]>=80:
            raise ValueError("Source workspace limit reached; reset the synthetic demo")
        previous=self.read("""MATCH (s:Source {source_key:$key,current:true})
            RETURN s.id ORDER BY s.id LIMIT 1""",{"key":key})
        self.write("""MATCH (s:Source {source_key:$key,current:true})
            SET s.current=false""",{"key":key})
        lines=self._write_source(wid,ident,key,digest,kind,title.strip(),reference.strip(),
                                 content,"PENDING_REVIEW","decision:"+wid,"project:"+wid)
        if previous:
            self.write("""MATCH (new:Source {id:$id}),(old:Source {id:$previous})
                MERGE (new)-[:REVISION_OF]->(old)""",{"id":ident,"previous":previous[0][0]})
        self.record_event("SOURCE_IMPORTED",f"{kind} '{title}' imported for review","knowledge-import",ident)
        return self.get_source(ident)

    def list_sources(self, wid: str) -> list[dict]:
        self.snapshot(wid)
        rows=self.read("""MATCH (s:Source)-[:ABOUT]->(w:Workflow {id:$wid})
            OPTIONAL MATCH (p:Passage)-[:EXCERPT_OF]->(s)
            RETURN s.id,s.kind,s.title,s.reference,s.review_status,
                   s.current,count(p),s.content ORDER BY s.kind,s.title,s.id""",{"wid":wid})
        return [{"id":i,"kind":k,"title":t,"reference":r,"review_status":status,
                 "current":current,"passage_count":count,"excerpt":(content or "")[:220]}
                for i,k,t,r,status,current,count,content in rows]

    def get_source(self, source_id: str) -> dict:
        rows=self.read("""MATCH (s:Source {id:$id})-[:ABOUT]->(w:Workflow)
            RETURN s.id,s.kind,s.title,s.reference,s.review_status,
                   s.current,s.content,w.id""",{"id":source_id})
        if not rows: raise KeyError("Source not found")
        sid,kind,title,ref,status,current,content,wid=rows[0]
        entries=self.read("""MATCH (p:Passage)-[:EXCERPT_OF]->(s:Source {id:$id})
            RETURN p.id,p.locator,p.line,p.quote ORDER BY p.line""",{"id":source_id})
        return {"id":sid,"kind":kind,"title":title,"reference":ref,
                "review_status":status,"current":current,"content":content,
                "workflow_id":wid,"passages":[{"id":i,"locator":loc,"line":ln,"quote":q} for i,loc,ln,q in entries]}

    def verify_source(self, source_id: str, actor: str) -> dict:
        source=self.get_source(source_id)
        if not source["current"]: raise ValueError("Superseded source cannot be verified")
        if source["review_status"]=="SYNTHETIC_VERIFIED": return source
        if source["review_status"]!="VERIFIED":
            self.write("""MATCH (s:Source {id:$id})-[:MENTIONS]->(d:Decision)
                SET s.review_status='VERIFIED',s.reviewed_by=$actor
                WITH s,d MATCH (p:Passage)-[:EXCERPT_OF]->(s)
                MERGE (p)-[:CITED_IN_REVIEW]->(d)""",{"id":source_id,"actor":actor})
            self.record_event("SOURCE_VERIFIED","Reviewer confirmed source association to the workflow decision",actor,source_id)
        return self.get_source(source_id)

    def search_evidence(self, wid: str, question: str) -> list[dict]:
        self.snapshot(wid)
        rows=self.read("""MATCH (p:Passage)-[:EXCERPT_OF]->(s:Source {current:true})-[:ABOUT]->(w:Workflow {id:$wid})
            RETURN p.id,p.locator,p.quote,s.id,s.kind,s.title,s.reference,s.review_status
            ORDER BY s.kind,p.line""",{"wid":wid})
        entries=[{"passage_id":pid,"locator":loc,"quote":q,"source_id":sid,"kind":k,
                  "title":title,"reference":ref,"review_status":status}
                 for pid,loc,q,sid,k,title,ref,status in rows]
        lower=question.lower()
        if "ticket" in lower:
            entries=[e for e in entries if e["kind"]=="TICKET"]
        elif "chat" in lower or "conversation" in lower or "handoff" in lower:
            entries=[e for e in entries if e["kind"]=="CONVERSATION"]
        elif "document" in lower or "playbook" in lower:
            entries=[e for e in entries if e["kind"]=="DOCUMENT"]
        return rank_passages(question,entries)

    def list_workflows(self) -> list[dict]:
        rows = self.read("""MATCH (w:Workflow) OPTIONAL MATCH (w)-[:HAS_STEP]->(s:Step)
                            RETURN w.id,w.name,w.department,w.criticality,w.description,count(s)
                            ORDER BY w.name""")
        return [{"id":i,"name":n,"department":d,"criticality":c,"description":desc,"step_count":count} for i,n,d,c,desc,count in rows]

    def list_people(self) -> list[dict]:
        return [{"id":i,"name":n,"team":t,"role":r} for i,n,t,r in self.read("""MATCH (p:Person)-[:MEMBER_OF]->(t:Team)
                         RETURN p.id,p.name,t.name,p.role ORDER BY p.name""")]

    def snapshot(self, workflow_id: str) -> dict:
        row = self.read("""MATCH (w:Workflow {id:$id}) RETURN w.id,w.name,w.department,w.criticality,w.description""", {"id":workflow_id})
        if not row:
            raise KeyError("Workflow not found")
        wid,name,department,criticality,description = row[0]
        step_rows = self.read("""MATCH (w:Workflow {id:$id})-[:HAS_STEP]->(s:Step)
                    MATCH (s)-[:REQUIRES_SKILL]->(skill:Skill)
                    MATCH (s)-[:REQUIRES_PERMISSION]->(perm:Permission)
                    RETURN s.id,s.short_id,s.name,s.position,skill.id,perm.id ORDER BY s.position""", {"id":workflow_id})
        steps = [{"id":sid,"short_id":short,"name":n,"position":pos,"skill":sk,"permission":perm}
                 for sid,short,n,pos,sk,perm in step_rows]
        sep_rows = self.read("""MATCH (w:Workflow {id:$id})-[:HAS_STEP]->(s:Step)
                        MATCH (s)-[:SEPARATE_FROM]->(other:Step) RETURN s.id,other.id""", {"id":workflow_id})
        person_rows = self.read("""MATCH (p:Person)-[:MEMBER_OF]->(t:Team)
                     RETURN p.id,p.name,t.name,p.role,p.active ORDER BY p.id""")
        people = {pid:{"id":pid,"name":n,"team":team,"role":role,"active":active,
                       "skills":[],"permissions":{}} for pid,n,team,role,active in person_rows}
        for pid,skill in self.read("MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) RETURN p.id,s.id"):
            if pid in people: people[pid]["skills"].append(skill)
        for pid,perm,state in self.read("MATCH (p:Person)-[g:GRANTED]->(q:Permission) RETURN p.id,q.id,g.state"):
            if pid in people: people[pid]["permissions"][perm] = state
        docs = [title for (title,) in self.read("""MATCH (d:Document)-[:DESCRIBES]->(w:Workflow {id:$id})
                        RETURN d.title ORDER BY d.title""", {"id":workflow_id})]
        decisions = [title for (title,) in self.read("""MATCH (d:Decision)-[:GOVERNS]->(w:Workflow {id:$id}) RETURN d.title""", {"id":workflow_id})]
        return {"workflow":{"id":wid,"name":name,"department":department,"criticality":criticality,"description":description},
                "steps":steps,"separation":[list(row) for row in sep_rows], "people":list(people.values()),
                "documents":docs,"decision":decisions[0] if decisions else None}

    def graph_view(self, workflow_id: str) -> dict:
        s=self.snapshot(workflow_id)
        nodes=[{"id":s["workflow"]["id"],"label":s["workflow"]["name"],"type":"workflow"}]
        edges=[]
        for step in s["steps"]:
            nodes.append({"id":step["id"],"label":step["name"],"type":"step"})
            edges.append({"source":s["workflow"]["id"],"target":step["id"],"label":"HAS_STEP"})
            for what,kind in [(step["skill"],"skill"),(step["permission"],"permission")]:
                ident=f"{kind}:{what}"
                if not any(n["id"]==ident for n in nodes):
                    nodes.append({"id":ident,"label":what,"type":kind})
                edges.append({"source":step["id"],"target":ident,"label":"REQUIRES"})
        relevant_skills={x["skill"] for x in s["steps"]}
        relevant_permissions={x["permission"] for x in s["steps"]}
        for person in s["people"]:
            if any(sk in person["skills"] for sk in relevant_skills):
                nodes.append({"id":person["id"],"label":person["name"],"type":"person", "detail":person["role"]})
                for skill in person["skills"]:
                    if skill in relevant_skills:
                        edges.append({"source":person["id"],"target":f"skill:{skill}","label":"HAS_SKILL"})
                for permission,state in person["permissions"].items():
                    if permission in relevant_permissions:
                        edges.append({"source":person["id"],"target":f"permission:{permission}",
                                      "label":f"GRANT {state}","grant_state":state})
        visible_sources=[source for source in self.list_sources(workflow_id) if source["current"]]
        for source in visible_sources:
            nodes.append({"id":source["id"],"label":source["title"],"type":"document",
                          "detail":source["kind"]+" · "+source["review_status"]})
            edges.append({"source":source["id"],"target":workflow_id,"label":"ABOUT"})
            edges.append({"source":source["id"],"target":"decision:"+workflow_id,
                          "label":"REVIEWED" if source["review_status"]!="PENDING_REVIEW" else "MENTIONS"})
            # Show exact, resolvable line evidence without overloading the diagram.
            citations=self.get_source(source["id"])["passages"][:2]
            for passage in citations:
                nodes.append({"id":passage["id"],"label":"Line "+str(passage["line"])+": "+passage["quote"][:48],
                              "type":"passage", "detail":passage["locator"]})
                edges.append({"source":passage["id"],"target":source["id"],"label":"EXCERPT_OF"})
        project_id="project:"+workflow_id
        nodes.append({"id":project_id,"label":s["workflow"]["name"]+" continuity","type":"project"})
        edges.append({"source":project_id,"target":workflow_id,"label":"DELIVERS"})
        if s["decision"]:
            decision_id="decision:"+workflow_id
            nodes.append({"id":decision_id,"label":s["decision"],"type":"decision"})
            edges.append({"source":decision_id,"target":workflow_id,"label":"GOVERNS"})
        for a,b in s["separation"]:
            edges.append({"source":a,"target":b,"label":"SEPARATE_FROM"})
        return {"nodes":nodes,"edges":edges,"documents":[x["title"] for x in visible_sources],"decision":s["decision"]}

    def add_document(self, workflow_id: str, title: str, content: str) -> dict:
        """Manual, explicitly scoped text ingestion; no unverified auto-extracted facts."""
        self.snapshot(workflow_id)  # rejects unknown workflow
        digest = hashlib.sha256((workflow_id + "\x00" + title + "\x00" + content).encode()).hexdigest()
        doc_id = "doc:imported:" + digest[:24]
        result = {"id":doc_id,"title":title,"source":"Manual sandbox import", "version":"1",
                  "excerpt":content[:240], "workflow_id":workflow_id}
        self.write("""MATCH (w:Workflow {id:$workflow})
                    MERGE (d:Document {id:$id}) SET d.title=$title,d.source=$source,
                    d.version='1',d.content=$content
                    MERGE (d)-[:DESCRIBES]->(w)""",
                   {"workflow":workflow_id,"id":doc_id,"title":title,"source":result["source"],
                    "content":content})
        self.record_event("SOURCE_CONNECTED",f"Linked document '{title}' to {workflow_id}","demo-analyst",doc_id)
        return result

    def list_documents(self, workflow_id:str) -> list[dict]:
        self.snapshot(workflow_id)
        rows=self.read("""MATCH (d:Document)-[:DESCRIBES]->(w:Workflow {id:$workflow})
                     RETURN d.id,d.title,d.source,d.version,d.content ORDER BY d.title""",
                     {"workflow":workflow_id})
        return [{"id":i,"title":t,"source":s,"version":v,"excerpt":(content or "")[:240]} for i,t,s,v,content in rows]

    def record_agent_run(self, workflow_id:str, question:str, result:dict):
        self.write("""MATCH (w:Workflow {id:$workflow})
                    CREATE (a:AgentRun {id:$id,question:$question,tool:$tool,
                         answer:$answer,sources_json:$sources})-[:CONTEXT_FOR]->(w)""",
                   {"workflow":workflow_id,"id":uuid.uuid4().hex,"question":question,
                    "tool":result["tool"],"answer":result["answer"],
                    "sources":encode(result["sources"])})

    def record_event(self, kind:str, message:str, actor:str, entity_id:str):
        self.write("""MERGE (counter:Sequence {id:'audit'})
                      ON CREATE SET counter.value=0
                      SET counter.value=counter.value+1
                      WITH counter
                      CREATE (e:AuditEvent {id:$id,kind:$kind,message:$message,
                               actor:$actor,entity_id:$entity,sequence:counter.value})""",
                   {"id":uuid.uuid4().hex,"kind":kind,"message":message,"actor":actor,"entity":entity_id})

    def audit(self) -> list[dict]:
        return [{"kind":kind,"message":msg,"actor":actor,"entity_id":eid} for kind,msg,actor,eid in self.read("""MATCH (e:AuditEvent)
                        RETURN e.kind,e.message,e.actor,e.entity_id ORDER BY e.sequence DESC LIMIT 50""")]

    def create_simulation(self, workflow_id:str, unavailable:list[str]) -> dict:
        snap=self.snapshot(workflow_id)
        known={p["id"] for p in snap["people"]}
        if not set(unavailable).issubset(known):
            raise ValueError("Unknown employee ID in unavailable list")
        output=analyze(snap, unavailable)
        result={"id":uuid.uuid4().hex,"workflow_id":workflow_id,"workflow_name":snap["workflow"]["name"],
                "status":"FEASIBLE" if output["feasible"] else "BLOCKED", **output}
        self.write("""MATCH (w:Workflow {id:$workflow})
                    MERGE (counter:Sequence {id:'simulations'})
                    ON CREATE SET counter.value=0
                    SET counter.value=counter.value+1
                    WITH w,counter
                    CREATE (s:Simulation {id:$id,payload:$payload,sequence:counter.value})-[:TESTS]->(w)""",
                   {"workflow":workflow_id,"id":result["id"],"payload":encode(result)})
        self.record_event("SIMULATION_RUN",f"{snap['workflow']['name']}: {result['status']}","simulation-engine",result["id"])
        return result

    def get_simulation(self, sim_id:str) -> dict:
        rows=self.read("MATCH (s:Simulation {id:$id}) RETURN s.payload",{"id":sim_id})
        if not rows: raise KeyError("Simulation not found")
        return json.loads(rows[0][0])

    def latest_simulations(self) -> list[dict]:
        rows=self.read("MATCH (s:Simulation) RETURN s.payload ORDER BY s.sequence DESC LIMIT 10")
        return [json.loads(r[0]) for r in rows]

    def propose_repair(self, sim_id:str) -> dict:
        sim=self.get_simulation(sim_id)
        suggestion=sim.get("repair")
        if not suggestion or not suggestion["feasible"]:
            raise ValueError("No safe, supported repair exists for this simulation")
        existing=self.read("MATCH (r:Repair {simulation_id:$sim}) RETURN r.payload",{"sim":sim_id})
        if existing: return json.loads(existing[0][0])
        proposal={"id":uuid.uuid4().hex,"simulation_id":sim_id,"workflow_id":sim["workflow_id"],
                  "status":"PENDING_APPROVAL","actions":suggestion["renewals"],
                  "expected_assignments":suggestion["assignments"],
                  "description":"Renew only existing, expired sandbox permission grants; require manager approval and a simulated drill."}
        self.write("""MATCH (s:Simulation {id:$sim})
                    MERGE (counter:Sequence {id:'repairs'})
                    ON CREATE SET counter.value=0
                    SET counter.value=counter.value+1
                    WITH s,counter
                    CREATE (r:Repair {id:$id,simulation_id:$sim,payload:$payload,sequence:counter.value})-[:ADDRESSES]->(s)""",
                   {"sim":sim_id,"id":proposal["id"],"payload":encode(proposal)})
        self.record_event("REPAIR_PROPOSED","Prepared policy-compliant access renewal proposal", "planner",proposal["id"])
        return proposal

    def get_repair(self, repair_id:str) -> dict:
        rows=self.read("MATCH (r:Repair {id:$id}) RETURN r.payload",{"id":repair_id})
        if not rows: raise KeyError("Repair not found")
        return json.loads(rows[0][0])

    def list_repairs(self) -> list[dict]:
        return [json.loads(row[0]) for row in self.read("MATCH (r:Repair) RETURN r.payload ORDER BY r.sequence DESC LIMIT 30")]

    def approve_repair(self, repair_id:str, actor:str) -> dict:
        if os.getenv("APP_MODE", "demo") != "demo":
            raise PermissionError("Access changes disabled outside the isolated demo")
        repair=self.get_repair(repair_id)
        if repair["status"] != "PENDING_APPROVAL":
            raise ValueError("Repair has already been applied or closed")
        sim=self.get_simulation(repair["simulation_id"])
        latest=self.snapshot(repair["workflow_id"])
        current=analyze(latest,sim["unavailable"])
        expected={(a["person_id"],a["permission"]) for a in repair["actions"]}
        actual={(a["person_id"],a["permission"]) for a in ((current.get("repair") or {}).get("renewals") or [])}
        if not expected or expected != actual:
            raise ValueError("Graph changed since planning; rerun simulation and reapprove")
        # Atomic graph write: validate all existing EXPIRED grants before updating ANY.
        # No grants are ever created. A failed precondition produces no updates.
        actions=[{"person":a["person_id"],"perm":a["permission"]} for a in repair["actions"]]
        previous_payload=encode(repair)
        repair["status"]="APPLIED_PENDING_DRILL"
        repair["approved_by"]=actor
        rows=self.write("""MATCH (r:Repair {id:$id, payload:$previous})
            WITH r,$actions AS actions
            UNWIND actions AS action
            MATCH (p:Person {id:action.person})-[g:GRANTED {state:'EXPIRED'}]->(q:Permission {id:action.perm})
            WITH r,actions,collect(g) AS grants
            WHERE size(grants)=size(actions)
            FOREACH (grant IN grants | SET grant.state='ACTIVE',grant.source='approved-sandbox-renewal')
            SET r.payload=$payload
            RETURN r.id""", {"id":repair_id,"previous":previous_payload,"actions":actions,"payload":encode(repair)})
        if not rows:
            raise ValueError("Access changed during approval; rerun the simulation")
        self.record_event("SANDBOX_REPAIR_APPLIED","Renewed existing demo grants after recorded approval",actor,repair_id)
        return repair

    def run_drill(self, repair_id:str) -> dict:
        repair=self.get_repair(repair_id)
        if repair["status"] not in ("APPLIED_PENDING_DRILL", "VERIFIED"):
            raise ValueError("Approve and apply the sandbox repair first")
        sim=self.get_simulation(repair["simulation_id"])
        solution=solve(self.snapshot(repair["workflow_id"]),sim["unavailable"])
        result={"id":uuid.uuid4().hex,"repair_id":repair_id,"simulation_id":sim["id"],
                "status":"PASSED" if solution["feasible"] else "FAILED",
                "assignments":solution["assignments"],
                "mode":"SANDBOX_ASSIGNMENT_CHECK_ONLY", "blockers":solution["blockers"]}
        self.write("""MATCH (r:Repair {id:$repair})
                    CREATE (d:Drill {id:$id,payload:$payload})-[:VERIFIES]->(r)""",
                   {"repair":repair_id,"id":result["id"],"payload":encode(result)})
        repair["status"]="VERIFIED" if result["status"]=="PASSED" else "APPLIED_PENDING_DRILL"
        repair["last_drill_id"]=result["id"]
        self.write("MATCH (r:Repair {id:$id}) SET r.payload=$payload",{"id":repair_id,"payload":encode(repair)})
        self.record_event("DRILL_"+result["status"],"Sandbox feasibility verified" if solution["feasible"] else "Sandbox validation blocked","drill-engine",repair_id)
        return result

    def overview(self) -> dict:
        workflows=self.list_workflows()
        simulations=self.latest_simulations()
        repairs=self.list_repairs()
        return {"organization":"Northstar Payments","workflows":workflows,
                "employees":len(self.list_people()),"teams":len(TEAMS),
                "simulations":simulations[:5],"repairs":repairs[:5],
                "blocked_simulations":sum(s["status"]=="BLOCKED" for s in simulations),
                "open_repairs":sum(r["status"]!="VERIFIED" for r in repairs)}
