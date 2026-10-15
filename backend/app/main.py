from __future__ import annotations

import os
import time
import secrets
import re
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .graph_store import GraphStore
from .agent import answer as agent_answer
from .knowledge import KINDS


@asynccontextmanager
async def lifespan(app: FastAPI):
    if len(os.getenv("INTERNAL_API_KEY", "")) < 32:
        raise RuntimeError("INTERNAL_API_KEY must be configured with a strong secret")
    last_error=None
    for _ in range(20):
        try:
            app.state.store=GraphStore()
            app.state.store.ensure_seeded()
            break
        except Exception as exc:
            last_error=exc
            time.sleep(1)
    else:
        raise RuntimeError(f"FalkorDB connection/seed unsuccessful: {last_error}")
    yield


app=FastAPI(title="ContinuityOS API", version="1.0.0", lifespan=lifespan,
            openapi_url=None, docs_url=None, redoc_url=None,
            description="FalkorDB-driven organizational continuity and sandbox workflow recovery")

@app.middleware("http")
async def internal_api_auth(request: Request, call_next):
    if request.url.path == "/api/health":
        return await call_next(request)
    token=request.headers.get("x-internal-api-key", "")
    expected=os.getenv("INTERNAL_API_KEY", "")
    if len(expected)<32 or not secrets.compare_digest(token, expected):
        return JSONResponse({"detail":"Unauthorized"},status_code=401,headers={"Cache-Control":"no-store"})
    response=await call_next(request)
    response.headers["Cache-Control"]="no-store"
    response.headers["X-Content-Type-Options"]="nosniff"
    return response


DEMO_GRAPH_RE = re.compile(r"^continuity_judge_[a-f0-9]{24}$")


def demo_mode_enabled() -> bool:
    return os.getenv("APP_MODE") == "demo" and os.getenv("ENABLE_JUDGE_DEMO") == "true"


def db(request: Request):
    role = request.headers.get("x-operator-role", "operator")
    if role == "demo":
        graph_name = request.headers.get("x-demo-graph", "")
        if not demo_mode_enabled() or not DEMO_GRAPH_RE.fullmatch(graph_name):
            raise HTTPException(status_code=403, detail="Invalid demo workspace")
        # The graph name comes exclusively from a signed frontend session through the
        # private service-key proxy, never from a browser-supplied request header.
        return GraphStore(graph_name=graph_name)
    if role != "operator":
        raise HTTPException(status_code=403, detail="Unrecognized access role")
    if request.headers.get("x-demo-graph"):
        raise HTTPException(status_code=403, detail="Operator cannot select guest graph")
    return app.state.store


@app.post("/api/demo/bootstrap", status_code=201)
def bootstrap(request: Request):
    if request.headers.get("x-operator-role") != "demo":
        raise HTTPException(status_code=403, detail="Demo context required")
    graph_name = request.headers.get("x-demo-graph", "")
    if not demo_mode_enabled() or not DEMO_GRAPH_RE.fullmatch(graph_name):
        raise HTTPException(status_code=403, detail="Invalid demo workspace")
    graph = GraphStore(graph_name=graph_name)
    try:
        graph.ensure_seeded()
    except Exception:
        # The client must not receive connection details or internal error messages.
        raise HTTPException(status_code=503, detail="Demo initialization unavailable") from None
    return {"status":"ready"}


class SimulationRequest(BaseModel):
    workflow_id:str=Field(min_length=1,max_length=100)
    unavailable:list[str]=Field(default_factory=list,max_length=40)

class DocumentRequest(BaseModel):
    title:str=Field(min_length=3,max_length=160)
    content:str=Field(min_length=10,max_length=5000)

class SourceRequest(BaseModel):
    kind:str=Field(pattern=r"^(DOCUMENT|TICKET|CONVERSATION)$")
    title:str=Field(min_length=3,max_length=160)
    content:str=Field(min_length=10,max_length=10000)
    reference:str=Field(default="",max_length=120)

class AgentRequest(BaseModel):
    message:str=Field(min_length=3,max_length=500)
    workflow_id:str=Field(min_length=1,max_length=100)


def endpoint(call, *args, **kwargs):
    try: return call(*args, **kwargs)
    except KeyError as e: raise HTTPException(status_code=404,detail=str(e)) from e
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e
    except PermissionError as e: raise HTTPException(status_code=403,detail=str(e)) from e


@app.get("/api/health")
def health(store:Annotated[GraphStore,Depends(db)]):
    store.read("RETURN 1")
    return {"status":"ok","database":"FalkorDB","mode":os.getenv("APP_MODE","demo")}

@app.get("/api/overview")
def overview(store:Annotated[GraphStore,Depends(db)]): return store.overview()

@app.get("/api/workflows")
def workflows(store:Annotated[GraphStore,Depends(db)]): return store.list_workflows()

@app.get("/api/people")
def people(store:Annotated[GraphStore,Depends(db)]): return store.list_people()

@app.get("/api/workflows/{workflow_id}")
def snapshot(workflow_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.snapshot,workflow_id)

@app.get("/api/workflows/{workflow_id}/graph")
def graph(workflow_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.graph_view,workflow_id)

@app.post("/api/simulations",status_code=201)
def simulate(body:SimulationRequest,store:Annotated[GraphStore,Depends(db)]):
    return endpoint(store.create_simulation,body.workflow_id,body.unavailable)

@app.get("/api/simulations")
def simulations(store:Annotated[GraphStore,Depends(db)]): return store.latest_simulations()

@app.get("/api/simulations/{simulation_id}")
def simulation(simulation_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.get_simulation,simulation_id)

@app.post("/api/simulations/{simulation_id}/repair",status_code=201)
def repair(simulation_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.propose_repair,simulation_id)

@app.get("/api/repairs")
def repairs(store:Annotated[GraphStore,Depends(db)]): return store.list_repairs()

@app.get("/api/repairs/{repair_id}")
def get_repair(repair_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.get_repair,repair_id)

@app.post("/api/repairs/{repair_id}/approve")
def approve(repair_id:str,request:Request,store:Annotated[GraphStore,Depends(db)]):
    operator=request.headers.get("x-operator-id", "").strip()
    if not 2 <= len(operator) <= 100:
        raise HTTPException(status_code=403,detail="Authenticated reviewer identity required")
    return endpoint(store.approve_repair,repair_id,operator)

@app.post("/api/repairs/{repair_id}/drill")
def drill(repair_id:str,store:Annotated[GraphStore,Depends(db)]): return endpoint(store.run_drill,repair_id)

@app.get("/api/audit")
def audit(store:Annotated[GraphStore,Depends(db)]): return store.audit()

@app.post("/api/demo/reset")
def reset(request:Request,store:Annotated[GraphStore,Depends(db)]):
    if request.headers.get("x-reset-confirmation") != "RESET_SYNTHETIC_DATA":
        raise HTTPException(status_code=403,detail="Explicit reset confirmation required")
    if os.getenv("APP_MODE","demo")!="demo": raise HTTPException(status_code=403,detail="Demo only")
    if request.headers.get("x-operator-role") == "demo" and not demo_mode_enabled():
        raise HTTPException(status_code=403,detail="Demo disabled")
    return endpoint(store.seed_demo)

@app.post("/api/agent/ask")
def ask(body:AgentRequest,store:Annotated[GraphStore,Depends(db)]):
    result=endpoint(agent_answer,store,body.workflow_id,body.message)
    store.record_agent_run(body.workflow_id,body.message,result)
    return result

@app.get("/api/workflows/{workflow_id}/documents")
def list_documents(workflow_id:str,store:Annotated[GraphStore,Depends(db)]):
    return endpoint(store.list_documents,workflow_id)

@app.post("/api/workflows/{workflow_id}/documents",status_code=201)
def connect_document(workflow_id:str,body:DocumentRequest,store:Annotated[GraphStore,Depends(db)]):
    if os.getenv("APP_MODE","demo")!="demo":
        raise HTTPException(status_code=403,detail="Manual import disabled outside demo mode")
    return endpoint(store.ingest_source,workflow_id,"DOCUMENT",body.title,body.content,"")


@app.get("/api/workflows/{workflow_id}/sources")
def sources(workflow_id:str,store:Annotated[GraphStore,Depends(db)]):
    return endpoint(store.list_sources,workflow_id)

@app.post("/api/workflows/{workflow_id}/sources",status_code=201)
def import_source(workflow_id:str,body:SourceRequest,store:Annotated[GraphStore,Depends(db)]):
    if os.getenv("APP_MODE")!="demo":
        raise HTTPException(status_code=403,detail="Source import restricted to isolated demo")
    return endpoint(store.ingest_source,workflow_id,body.kind,body.title,body.content,body.reference)

@app.get("/api/sources/{source_id}")
def source_detail(source_id:str,store:Annotated[GraphStore,Depends(db)]):
    return endpoint(store.get_source,source_id)

@app.post("/api/sources/{source_id}/verify")
def verify_source(source_id:str,request:Request,store:Annotated[GraphStore,Depends(db)]):
    if os.getenv("APP_MODE")!="demo":
        raise HTTPException(status_code=403,detail="Source review restricted to isolated demo")
    reviewer=request.headers.get("x-operator-id","").strip()
    if len(reviewer)<2 or len(reviewer)>100:
        raise HTTPException(status_code=403,detail="Authenticated reviewer required")
    return endpoint(store.verify_source,source_id,reviewer)
