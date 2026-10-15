"""Guardrails for the guest graph maintenance tool: only guest namespaces, confirmations required."""
from app import maintenance


class FakeGraph:
    def __init__(self, name, log):
        self.name=name
        self.log=log
    def delete(self):
        self.log.append(self.name)


class FakeClient:
    def __init__(self, log):
        self.log=log
    def select_graph(self, name):
        return FakeGraph(name, self.log)


class FakeStore:
    def __init__(self, names):
        self.names=list(names)
        self.log=[]
    @property
    def client(self):
        return FakeClient(self.log)
    def list_graph_names(self):
        return list(self.names)
    def read(self, *args):
        return [[0]]


A='continuity_judge_'+'a'*24
B='continuity_judge_'+'b'*24


def test_refuses_non_guest_graph_names():
    store=FakeStore(['continuity_demo'])
    assert maintenance.command_delete(store,['continuity_demo'],True)==2
    assert store.log==[]


def test_dry_run_deletes_nothing_then_deletes_only_guests():
    store=FakeStore([A,B,'continuity_demo'])
    assert maintenance.judge_graphs(store)==[A,B]
    assert maintenance.command_delete(store, maintenance.judge_graphs(store), False)==0
    assert store.log==[]
    assert maintenance.command_delete(store, maintenance.judge_graphs(store), True)==0
    assert store.log==[A,B]


def test_missing_graphs_are_skipped():
    store=FakeStore([])
    assert maintenance.command_delete(store,[A],True)==0
    assert store.log==[]
