"""Regression checks for the mandatory internal boundary and timestamp-free payloads."""
import os
from fastapi.testclient import TestClient
from app.main import app
from app.sample import demo_snapshot
from app.solver import analyze

class StubGraph:
    def list_people(self):
        return [{"id":"p01"}]
    def approve_repair(self, repair_id, actor):
        return {"id":repair_id,"approved_by":actor}
    def read(self, *args):
        return [[1]]


def test_api_refuses_unauthorized_reads(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "x"*48)
    app.state.store=StubGraph()
    client=TestClient(app)
    assert client.get('/api/people').status_code == 401
    assert client.get('/api/people',headers={'x-internal-api-key':'wrong'}).status_code == 401
    assert client.get('/api/people',headers={'x-internal-api-key':'x'*48}).json()==[{"id":"p01"}]
    assert client.get('/api/health').status_code == 200


def test_review_identity_can_only_come_from_trusted_service_request(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "x"*48)
    app.state.store=StubGraph()
    client=TestClient(app)
    key={'x-internal-api-key':'x'*48}
    assert client.post('/api/repairs/r1/approve',headers=key,json={'actor':'Pretend CEO'}).status_code==403
    assert client.post('/api/repairs/r1/approve',headers={**key,'x-operator-id':'Operator One'},json={'actor':'Pretend CEO'}).json()['approved_by']=='Operator One'


def test_demo_reset_requires_separate_confirmation(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "x"*48)
    app.state.store=StubGraph()
    client=TestClient(app)
    assert client.post('/api/demo/reset',headers={'x-internal-api-key':'x'*48}).status_code==403


def test_business_solver_has_no_calendar_properties():
    payload=analyze(demo_snapshot('enterprise-refund'),['p02'])
    assert 'as_of' not in payload
    assert all(state in ('ACTIVE','EXPIRED') for p in demo_snapshot('enterprise-refund')['people'] for state in p['permissions'].values())
    assert 'created_at' not in payload and 'checked_at' not in payload


def test_guest_graph_requires_valid_scope(monkeypatch):
    import importlib
    module=importlib.import_module('app.main')
    monkeypatch.setenv('INTERNAL_API_KEY','x'*48)
    monkeypatch.setenv('APP_MODE','demo')
    monkeypatch.setenv('ENABLE_JUDGE_DEMO','true')
    app.state.store=StubGraph()
    selected=[]
    class TenantGraph(StubGraph):
        def __init__(self,graph_name):selected.append(graph_name)
        def ensure_seeded(self):selected.append('seeded')
    monkeypatch.setattr(module,'GraphStore',TenantGraph)
    client=TestClient(app)
    guest={'x-internal-api-key':'x'*48,'x-operator-role':'demo',
           'x-demo-graph':'continuity_judge_'+'a'*24}
    assert client.get('/api/people',headers=guest).json()==[{'id':'p01'}]
    assert selected==[guest['x-demo-graph']]
    assert client.get('/api/people',headers={**guest,'x-demo-graph':'continuity_demo'}).status_code==403
    assert client.get('/api/people',headers={**guest,'x-demo-graph':'continuity_judge_'+'../bad'}).status_code==403
    assert client.get('/api/people',headers={**guest,'x-operator-role':'operator'}).status_code==403
    assert client.post('/api/demo/bootstrap',headers=guest).status_code==201
    assert selected[-2:]==[guest['x-demo-graph'],'seeded']
    assert client.post('/api/demo/bootstrap',headers={'x-internal-api-key':'x'*48}).status_code==403
    assert client.post('/api/demo/bootstrap',headers={**guest,'x-internal-api-key':'bad'}).status_code==401


def test_disabled_demo_refuses_scope(monkeypatch):
    monkeypatch.setenv('INTERNAL_API_KEY','x'*48)
    monkeypatch.setenv('APP_MODE','demo')
    monkeypatch.setenv('ENABLE_JUDGE_DEMO','false')
    app.state.store=StubGraph()
    client=TestClient(app)
    guest={'x-internal-api-key':'x'*48,'x-operator-role':'demo','x-demo-graph':'continuity_judge_'+'a'*24}
    assert client.get('/api/people',headers=guest).status_code==403
    assert client.post('/api/demo/bootstrap',headers=guest).status_code==403


def test_source_import_requires_valid_kind_and_auth(monkeypatch):
    monkeypatch.setenv('INTERNAL_API_KEY','x'*48)
    monkeypatch.setenv('APP_MODE','demo')
    app.state.store=StubGraph()
    client=TestClient(app)
    body={'kind':'TICKET','title':'Policy ticket','content':'Follow documented approval policy','reference':'TASK-10'}
    assert client.post('/api/workflows/enterprise-refund/sources',json=body).status_code==401
    assert client.post('/api/workflows/enterprise-refund/sources',json={**body,'kind':'INVALID'},headers={'x-internal-api-key':'x'*48}).status_code==422


def test_source_verification_requires_reviewer(monkeypatch):
    monkeypatch.setenv('INTERNAL_API_KEY','x'*48)
    monkeypatch.setenv('APP_MODE','demo')
    app.state.store=StubGraph()
    client=TestClient(app)
    assert client.post('/api/sources/src:record/verify',headers={'x-internal-api-key':'x'*48}).status_code==403
