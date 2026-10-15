"""Graph-grounded continuity agent: inspect -> choose tool -> record safe sandbox checks when asked.

The deterministic path works without API keys. Optional OpenAI-compatible routing,
when explicitly configured, picks among a fixed whitelist of safe tools; evidence
and feasibility always come from FalkorDB/solver, never from model assertions.
"""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from .solver import analyze, options

SAFE_TOOLS={"ownership","eligible_executors","continuity_check","record_continuity_check","evidence"}


def _route(message:str) -> str:
    q=message.lower()
    if any(x in q for x in ("run and save", "record a simulation", "save a simulation", "run a simulation", "run a check")):
        return "record_continuity_check"
    if any(x in q for x in ("what if","survive","unavailable","absent","away","simulate","blocked","fails","fail")):
        return "continuity_check"
    if any(x in q for x in ("who can","eligible","permission","qualified","replace","backup")):
        return "eligible_executors"
    if any(x in q for x in ("document","evidence","policy","decision","source","why","ticket","conversation","chat","quote","citation")):
        return "evidence"
    return "ownership"


def _optional_llm_router(message:str) -> str | None:
    key=os.getenv("OPENAI_API_KEY")
    if not key or os.getenv("ENABLE_LLM_ROUTER","false").lower()!="true":
        return None
    data={"model":os.getenv("OPENAI_MODEL","gpt-4o-mini"),
          "messages":[{"role":"system","content":"Return only a JSON object with key 'tool' chosen from: ownership, eligible_executors, continuity_check, record_continuity_check, evidence. Use record_continuity_check only when the user explicitly asks to save or run and record a simulation. Do not return facts or instructions."},
                      {"role":"user","content":message[:500]}],
          "response_format":{"type":"json_object"},"temperature":0}
    req=Request("https://api.openai.com/v1/chat/completions",data=json.dumps(data).encode(),
                headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=8) as r:
            answer=json.load(r)
        tool=json.loads(answer["choices"][0]["message"]["content"])["tool"]
        return tool if tool in SAFE_TOOLS else None
    except (OSError,KeyError,ValueError,TypeError,IndexError):
        return None


def answer(store, workflow_id:str, message:str) -> dict:
    snap=store.snapshot(workflow_id)
    local_tool=_route(message)
    # Explicitly requested persistence cannot be silently downgraded by LLM routing.
    tool=local_tool if local_tool=="record_continuity_check" else (_optional_llm_router(message) or local_tool)
    workflow=snap["workflow"]
    sources=[{"type":"workflow","id":workflow_id,"label":workflow["name"]}]
    trace=[{"step":"FalkorDB","detail":"Loaded workflow, people, skills, grants, documents and policy edges."},
           {"step":"Routing","detail":f"Selected graph-grounded tool: {tool}"}]
    if tool=="ownership":
        owners=[p for p in snap["people"] if p["team"]==workflow["department"]]
        text=(f"{workflow['department']} owns {workflow['name']}. The workflow has {len(snap['steps'])} required steps, "
              f"and {len(owners)} people belong to the owning department in the company graph. "
              "Ownership is different from authorization to execute an individual step.")
        sources.append({"type":"team","id":workflow["department"],"label":workflow["department"]})
    elif tool=="eligible_executors":
        candidates=options(snap,[],False)
        phrases=[]
        for step,people in zip(snap["steps"],candidates):
            names=", ".join(p["person_name"] for p in people) if people else "none"
            phrases.append(f"{step['name']}: {names}")
            sources.append({"type":"step","id":step["id"],"label":step["name"]})
        text="Currently authorized and skilled candidates by step (based on current sandbox authorization records): " + "; ".join(phrases) + ". Combined assignments must still satisfy separation-of-duties rules."
    elif tool=="evidence":
        if hasattr(store,"search_evidence"):
            entries=store.search_evidence(workflow_id,message)
            if entries:
                # Quote real stored text, never generate unsupported semantic summaries.
                quotes=[]
                for e in entries[:5]:
                    verified=e["review_status"] in ("VERIFIED","SYNTHETIC_VERIFIED")
                    label=f"{e['title']} ({e['kind']})"
                    quotes.append(f"{label} [{e['locator']}]: \"{e['quote'][:280]}\"" +
                                  ("" if verified else " [unverified import]"))
                    sources.append({"type":e["kind"].lower(),"id":e["source_id"],
                                    "passage_id":e["passage_id"],"locator":e["locator"],
                                    "quote":e["quote"],"review_status":e["review_status"],"label":label})
                text="Relevant passages retrieved from FalkorDB (verbatim, not independently fact-checked): " + " | ".join(quotes)
            else:
                text="No source passages match the request. I cannot infer an answer without supporting records. Try a more specific term or import and review a source."
            trace.append({"step":"Passage retrieval","detail":"Selected stored source-line citations using literal lexical overlap; unverified imports are marked."})
        else:
            # Unit fixtures without a database expose only legacy document titles.
            docnames=", ".join(snap["documents"]) or "none"
            text=f"The graph associates {workflow['name']} with these synthetic source records: {docnames}. Governance decision: {snap['decision'] or 'not recorded'}. These are seeded references, not verified external documents."
            sources.extend({"type":"document","id":workflow_id,"label":n} for n in snap["documents"])
    else:
        exclusions=[]
        q=message.lower()
        # Only exact name matches; no guessing from partial names.
        for p in snap["people"]:
            if p["name"].lower() in q or p["id"].lower() in q.split():
                exclusions.append(p["id"])
                sources.append({"type":"person","id":p["id"],"label":p["name"]})
        result=store.create_simulation(workflow_id,exclusions) if tool=="record_continuity_check" else analyze(snap,exclusions)
        if tool=="record_continuity_check":
            sources.append({"type":"simulation","id":result["id"],"label":"Saved sandbox continuity assessment"})
            trace.append({"step":"FalkorDB write","detail":"Persisted a new simulation for review and audit."})
        text=(f"With {', '.join(p['name'] for p in snap['people'] if p['id'] in exclusions) if exclusions else 'no explicitly identified absences'}, "
              f"{workflow['name']} is {'feasible' if result['feasible'] else 'blocked'} in a sandbox assignment check. "
              + result['explanation'])
        if result.get("repair"):
            steps=[f"renew {r['permission']} for {next(p['name'] for p in snap['people'] if p['id']==r['person_id'])}" for r in result['repair']['renewals']]
            text+=" Proposed safe recovery: "+", ".join(steps)+". Approval and a new drill are required."
        trace.append({"step":"Constraint engine","detail":result["solver"]+" checked eligibility and separation of duties."})
        if tool=="record_continuity_check": text+=" This result was saved in the graph and is available under simulations and audit history."
    # Non-evidence tools also expose documentary context where available.
    # Authorization and feasibility still derive from grant/skill/solver state,
    # not from the document's language.
    if tool != "evidence" and hasattr(store,"search_evidence"):
        policy_context=store.search_evidence(workflow_id,"independent approval permissions control")
        for record in policy_context[:2]:
            sources.append({"type":"contextual_"+record["kind"].lower(),
                            "id":record["source_id"],"passage_id":record["passage_id"],
                            "label":record["title"],"locator":record["locator"],
                            "quote":record["quote"],"review_status":record["review_status"]})
        if policy_context:
            trace.append({"step":"Evidence context","detail":"Linked documentary passages are context, not proof of current grant state."})
    return {"tool":tool,"answer":text,"sources":sources,"trace":trace,
            "disclaimer":"Synthetic organizational records. No real permissions, payments or decisions were changed."}
