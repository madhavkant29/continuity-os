"""Offline contract tests for citations, source revisions and agent grounding."""
from app.knowledge import passages, source_identity, rank_passages
from app.graph_store import GraphStore
from app.agent import answer
from app.sample import demo_snapshot


def test_original_line_numbers_and_stable_anchors():
    original="First statement\n\n  Second statement  \nThird statement"
    found=passages(original,"src:demo")
    assert [p["line"] for p in found]==[1,3,4]
    assert [p["locator"] for p in found]==["src:demo#L1","src:demo#L3","src:demo#L4"]
    assert found[1]["quote"]=="  Second statement  "


def test_repeated_source_is_idempotent_and_edit_preserves_identity_group():
    a,key,hash_a=source_identity("refund","TICKET","Ticket title","INC-42","Original evidence")
    b,key2,hash_b=source_identity("refund","TICKET","Changed title","INC-42","Revised evidence")
    assert a!=b and key==key2 and hash_a!=hash_b
    assert source_identity("refund","TICKET","Ticket title","INC-42","Original evidence")[0]==a


def test_search_requires_matching_evidence():
    entries=[{"locator":"src:a#L1","quote":"Treasury has payout approval","title":"Permission record","reference":""},
             {"locator":"src:b#L1","quote":"Finance validates refund","title":"Review record","reference":""}]
    assert rank_passages("payout authorization Treasury",entries)[0]["locator"]=="src:a#L1"
    assert rank_passages("quantum submarine",entries)==[]


class FakeGraphForAgent:
    def snapshot(self, wid):
        return demo_snapshot(wid)

    def search_evidence(self,wid,message):
        return [{"passage_id":"src:x:L2","locator":"src:x#L2","quote":"Require independent refund approval.",
                 "source_id":"src:x","kind":"TICKET","title":"Governance task","reference":"POL-1",
                 "review_status":"VERIFIED"}]


def test_agent_quotes_exact_stored_source_line():
    response=answer(FakeGraphForAgent(),"enterprise-refund","What does the governance ticket say?")
    assert response["tool"]=="evidence"
    assert "Require independent refund approval." in response["answer"]
    assert response["sources"][1]["locator"]=="src:x#L2"
    assert response["sources"][1]["quote"]=="Require independent refund approval."


def test_agent_preserves_pending_status():
    class Pending(FakeGraphForAgent):
        def search_evidence(self,wid,message):
            rows=super().search_evidence(wid,message)
            rows[0]["review_status"]="PENDING_REVIEW"
            return rows
    result=answer(Pending(),"enterprise-refund","What is the evidence?")
    assert "unverified import" in result["answer"]


def test_import_source_never_self_verifies():
    class CapturedStore(GraphStore):
        def __init__(self):self.statements=[]
        def snapshot(self,wid):return {"workflow":{"id":wid}}
        def read(self,q,params=None):return []
        def write(self,q,params=None):
            self.statements.append((q,params or {}));return []
        def get_source(self,identifier):return {"id":identifier,"review_status":"PENDING_REVIEW"}
        def record_event(self,*args):pass
    s=CapturedStore()
    result=s.ingest_source("enterprise-refund","CONVERSATION","Operations chat",
        "Lead: Who can approve this request?\nAuditor: Check the access registry.","CHAT-53")
    assert result["review_status"]=="PENDING_REVIEW"
    assert any("PENDING_REVIEW" in str(values) for _,values in s.statements)
    assert any("EXCERPT_OF" in q for q,_ in s.statements)
    assert not any("CITED_IN_REVIEW" in q for q,_ in s.statements)


def test_existing_version_is_returned_without_an_extra_write():
    from app.knowledge import source_identity
    title="Test ticket";text="Require independently authorized escalation.";wid="enterprise-refund"
    identifier,_,_=source_identity(wid,"TICKET",title,"TASK-10",text)
    class AlreadyStored(GraphStore):
        def __init__(self):self.write_count=0
        def snapshot(self,wid):pass
        def read(self,q,p=None):return [[identifier]]
        def write(self,q,p=None):self.write_count+=1
        def get_source(self,identifier):return {"id":identifier}
    store=AlreadyStored()
    assert store.ingest_source(wid,"TICKET",title,text,"TASK-10")["id"]==identifier
    assert store.write_count==0
