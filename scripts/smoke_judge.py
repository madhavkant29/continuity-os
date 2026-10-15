"""Live browser-path smoke checks for the one-click judge experience.

Requires a running local Docker stack with ENABLE_JUDGE_DEMO=true.
Only modifies isolated fictional judge graphs; it does not touch the operator graph.
"""
from __future__ import annotations
import json
import os
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, Request

BASE=os.getenv('CONTINUITY_PUBLIC_ORIGIN','http://localhost:3000').rstrip('/')


def new_judge():
    opener=build_opener(HTTPCookieProcessor(CookieJar()))
    def request(route, method='GET', data=None, headers=None):
        body=None if data is None else json.dumps(data).encode()
        base_headers={'Origin':BASE,'Content-Type':'application/json'}
        base_headers.update(headers or {})
        req=Request(BASE+route,data=body,method=method,headers=base_headers)
        with opener.open(req,timeout=30) as response:
            return json.load(response)
    return request


def main():
    a,b=new_judge(),new_judge()
    assert a('/api/auth/demo-status')['enabled']
    assert a('/api/auth/demo', 'POST', {})['ok']
    assert b('/api/auth/demo', 'POST', {})['ok']
    assert a('/api/auth/me')['role']=='demo'
    assert len(a('/api/people'))==30
    assert len(b('/api/people'))==30
    # Source-level organizational knowledge must persist in FalkorDB and be cited.
    sources=a('/api/workflows/enterprise-refund/sources')
    assert any(s['kind']=='DOCUMENT' for s in sources)
    assert any(s['kind']=='TICKET' for s in sources)
    assert any(s['kind']=='CONVERSATION' for s in sources)
    source=a('/api/workflows/enterprise-refund/sources','POST',{
        'kind':'TICKET','title':'Judge continuity ticket','reference':'JUDGE-TASK-1',
        'content':'Incident: refund approver unavailable.\nControl: use a separate authorized approver.'})
    assert source['review_status']=='PENDING_REVIEW'
    assert source['passages'][0]['locator'].endswith('#L1')
    assert len(a('/api/workflows/enterprise-refund/sources'))==len(sources)+1
    assert len(b('/api/workflows/enterprise-refund/sources'))==len(sources)
    verified=a('/api/sources/'+source['id']+'/verify','POST',{})
    assert verified['review_status']=='VERIFIED'
    citation=a('/api/agent/ask','POST',{'workflow_id':'enterprise-refund',
                 'message':'What does the ticket say about approver?'})
    assert any(src.get('locator') and src.get('quote') for src in citation['sources'])
    graph=a('/api/workflows/enterprise-refund/graph')
    assert any(n['type']=='project' for n in graph['nodes'])
    assert any(n['type']=='passage' for n in graph['nodes'])
    sim=a('/api/simulations','POST',{'workflow_id':'enterprise-refund','unavailable':['p02']})
    assert sim['status']=='BLOCKED'
    assert len(a('/api/simulations'))==1
    assert b('/api/simulations')==[], 'Judge B must not see Judge A records'
    a('/api/demo/reset','POST',{},headers={'x-reset-confirmation':'RESET_SYNTHETIC_DATA'})
    assert a('/api/simulations')==[]
    assert b('/api/simulations')==[]
    print('PASS: judge login, isolated source ingestion, reviewed evidence, exact citations, graph context, simulation and reset')

if __name__=='__main__':main()
