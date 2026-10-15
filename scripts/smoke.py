"""Live integration smoke script; requires Docker Compose and real FalkorDB.

This is intentionally NOT part of the offline unit test suite.
Running the script resets the synthetic sandbox organization.
"""
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.getenv("CONTINUITY_BACKEND_ORIGIN", "http://localhost:8000").rstrip("/") + "/api"
# No secrets in code. Read the generated local env only for this smoke harness.
values={}
config=Path(__file__).resolve().parents[1]/'.env'
if config.exists():
    for line in config.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);values[k]=v
SECRET=os.getenv('INTERNAL_API_KEY') or values.get('INTERNAL_API_KEY','')


def call(route, method="GET", body=None):
    data=None if body is None else json.dumps(body).encode()
    req=Request(BASE+route,data=data,method=method,headers={"Content-Type":"application/json",
        "x-internal-api-key":SECRET,"x-operator-id":"Smoke Test Operator",
        "x-reset-confirmation":"RESET_SYNTHETIC_DATA"})
    with urlopen(req,timeout=20) as response:
        return json.loads(response.read())


def main():
    print("Checking FalkorDB-backed API...")
    assert call("/health")["database"] == "FalkorDB"
    print("Resetting SYNTHETIC sandbox only")
    call("/demo/reset", "POST")
    data=call("/overview")
    assert data["employees"]==30 and len(data["workflows"])==5
    print("Running Ava Shah absence scenario")
    sim=call("/simulations", "POST", {"workflow_id":"enterprise-refund","unavailable":["p02"]})
    assert sim["status"]=="BLOCKED" and sim["repair"] is not None
    print("Creating graph-persisted review")
    repair=call(f"/simulations/{sim['id']}/repair","POST")
    assert repair["status"]=="PENDING_APPROVAL"
    print("Approving *demo* permission renewal")
    approved=call(f"/repairs/{repair['id']}/approve","POST",{})
    assert approved["status"]=="APPLIED_PENDING_DRILL"
    print("Checking repaired feasibility in sandbox")
    drill=call(f"/repairs/{repair['id']}/drill","POST")
    assert drill["status"]=="PASSED"
    assert call(f"/repairs/{repair['id']}")["status"]=="VERIFIED"
    response=call("/agent/ask", "POST", {"workflow_id":"enterprise-refund","message":"Who can approve this refund?"})
    assert response["sources"]
    assert call("/audit")
    print("PASS: actual graph persistence, constraints, proposal, demo approval, drill, agent, audit")
    print("CAUTION: sandbox data has been mutated. Reset through the UI for another demo.")


if __name__=="__main__":
    try: main()
    except (AssertionError,HTTPError,URLError) as err:
        print("FAIL:",err,file=sys.stderr)
        sys.exit(1)
