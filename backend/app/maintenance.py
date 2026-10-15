"""Operator maintenance for persistent synthetic judge graphs.

Run inside the deployed backend container, which already has database
credentials and network access:

    docker compose exec backend python -m app.maintenance list
    docker compose exec backend python -m app.maintenance delete-all --yes
    docker compose exec backend python -m app.maintenance delete continuity_judge_<id> --yes

Only graphs matching the guest namespace pattern can be touched. The operator
graph and any other database is refused. Guests can recreate their workspace
by signing in again, so cleanup is safe for abandoned fictional demos.
"""
from __future__ import annotations

import argparse
import sys

from .graph_store import JUDGE_GRAPH_RE, GraphStore


def judge_graphs(store: GraphStore) -> list[str]:
    return sorted(name for name in store.list_graph_names() if JUDGE_GRAPH_RE.fullmatch(name))


def command_list(store: GraphStore) -> int:
    names = judge_graphs(store)
    print(f"{len(names)} judge graph(s) present")
    for name in names:
        try:
            rows = store.client.select_graph(name).ro_query("MATCH (n) RETURN count(n)").result_set
            nodes = rows[0][0] if rows else 0
        except Exception as exc:  # noqa: BLE001 - report and continue
            nodes = f"unreadable ({exc})"
        print(f"  {name}: {nodes} nodes")
    return 0


def command_delete(store: GraphStore, names: list[str], confirmed: bool) -> int:
    if not names:
        print("No graph names given", file=sys.stderr)
        return 2
    invalid = [n for n in names if not JUDGE_GRAPH_RE.fullmatch(n)]
    if invalid:
        print(f"Refusing non-judge graph names: {invalid}", file=sys.stderr)
        return 2
    existing = set(store.list_graph_names())
    targets = [n for n in names if n in existing]
    missing = [n for n in names if n not in existing]
    if missing:
        print(f"Not present (skipped): {missing}")
    if not confirmed:
        print(f"Dry run: would delete {len(targets)} graph(s): {targets}")
        print("Re-run with --yes to delete.")
        return 0
    for name in targets:
        store.client.select_graph(name).delete()
        print(f"deleted {name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show judge graphs and node counts")
    delete_all = sub.add_parser("delete-all", help="delete every guest judge graph")
    delete_all.add_argument("--yes", action="store_true", help="confirm deletion")
    delete = sub.add_parser("delete", help="delete specific guest judge graphs")
    delete.add_argument("names", nargs="+")
    delete.add_argument("--yes", action="store_true", help="confirm deletion")
    args = parser.parse_args(argv)

    store = GraphStore()
    if args.command == "list":
        return command_list(store)
    if args.command == "delete-all":
        names = judge_graphs(store)
        if not names:
            print("No judge graphs to delete")
            return 0
        return command_delete(store, names, args.yes)
    return command_delete(store, args.names, args.yes)


if __name__ == "__main__":
    raise SystemExit(main())
