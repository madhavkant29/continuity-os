from app.agent import answer
from app.sample import demo_snapshot

class FakeGraph:
    def snapshot(self, wid):
        return demo_snapshot(wid)


def test_agent_uses_graph_context_and_evidence():
    response=answer(FakeGraph(),"enterprise-refund","Which documents support this workflow?")
    assert response['tool']=='evidence'
    assert 'Refund operations playbook' in response['answer']
    assert response['sources'][0]['id']=='enterprise-refund'


def test_agent_reports_graph_grounded_disruption():
    response=answer(FakeGraph(),"enterprise-refund","What if Ava Shah is away?")
    assert response['tool']=='continuity_check'
    assert 'blocked' in response['answer'].lower()
    assert 'REFUND_APPROVE' in response['answer']
    assert any(s['type']=='person' and s['id']=='p02' for s in response['sources'])


def test_agent_can_save_requested_simulation_to_graph():
    from app.solver import analyze
    class WritingGraph(FakeGraph):
        def __init__(self): self.calls=[]
        def create_simulation(self,wid,unavailable):
            self.calls.append((wid,unavailable))
            return {"id":"sim-graph-record",**analyze(self.snapshot(wid),unavailable)}
    graph=WritingGraph()
    response=answer(graph,"enterprise-refund","Run and save an Ava Shah absence check")
    assert response["tool"]=="record_continuity_check"
    assert graph.calls==[("enterprise-refund",["p02"])]
    assert any(s["type"]=="simulation" for s in response["sources"])
    assert "saved" in response["answer"].lower()
