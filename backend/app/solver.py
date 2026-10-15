"""Deterministic workflow satisfiability and least-change repair solver.

CP-SAT is preferred in the deployment. A small exhaustive solver is retained for
reproducible unit tests in environments without OR-Tools; workflows are capped.
"""
from __future__ import annotations

from itertools import product
from typing import Any

try:
    from ortools.sat.python import cp_model
except ImportError:  # unit-test portability
    cp_model = None


def options(snapshot: dict, unavailable: list[str], allow_renewal: bool) -> list[list[dict]]:
    by_step = []
    for step in snapshot["steps"]:
        candidates = []
        for person in snapshot["people"]:
            if person["id"] in unavailable or not person.get("active", True):
                continue
            if step["skill"] not in person["skills"]:
                continue
            grant_state = person["permissions"].get(step["permission"])
            if not grant_state:
                continue  # Missing access must NEVER be granted automatically.
            expired = grant_state == "EXPIRED"
            if grant_state not in ("ACTIVE", "EXPIRED"):
                continue
            if expired and not allow_renewal:
                continue
            candidates.append({"person_id":person["id"], "person_name":person["name"],
                               "permission":step["permission"], "renew":expired})
        by_step.append(sorted(candidates, key=lambda c: c["person_id"]))
    return by_step


def _valid(assignments: list[dict], snapshot: dict) -> bool:
    mapping = {s["id"]: a["person_id"] for s,a in zip(snapshot["steps"], assignments)}
    return all(mapping[a] != mapping[b] for a,b in snapshot["separation"])


def _exhaustive(snapshot: dict, candidate_lists: list[list[dict]]) -> list[dict] | None:
    if any(not x for x in candidate_lists):
        return None
    if len(snapshot["steps"]) > 8:
        raise ValueError("Exhaustive mode limited to eight steps; install OR-Tools for larger workflows")
    best = None
    best_key = None
    for assignment in product(*candidate_lists):
        if not _valid(list(assignment), snapshot):
            continue
        renew = {(a["person_id"],a["permission"]) for a in assignment if a["renew"]}
        key = (len(renew), tuple(a["person_id"] for a in assignment))
        if best_key is None or key < best_key:
            best, best_key = list(assignment), key
    return best


def _cp_sat(snapshot: dict, candidate_lists: list[list[dict]]) -> tuple[list[dict] | None, bool]:
    if any(not x for x in candidate_lists):
        return None, False
    model = cp_model.CpModel()
    variables = {}
    renewal = {}
    for i, candidates in enumerate(candidate_lists):
        for j, cand in enumerate(candidates):
            variables[i,j] = model.NewBoolVar(f"assign_{i}_{j}")
            if cand["renew"]:
                key = (cand["person_id"], cand["permission"])
                if key not in renewal:
                    renewal[key] = model.NewBoolVar(f"renew_{key[0]}_{key[1]}")
                model.Add(variables[i,j] <= renewal[key])
        model.Add(sum(variables[i,j] for j in range(len(candidates))) == 1)
    by_id = {s["id"]:i for i,s in enumerate(snapshot["steps"])}
    for first, second in snapshot["separation"]:
        a, b = by_id[first], by_id[second]
        for j,c in enumerate(candidate_lists[a]):
            for k,d in enumerate(candidate_lists[b]):
                if c["person_id"] == d["person_id"]:
                    model.Add(variables[a,j] + variables[b,k] <= 1)
    # Minimize number of restored expired grants; secondarily prefer stable employee IDs.
    model.Minimize(100000 * sum(renewal.values()) + sum((j+1)*variables[i,j] for (i,j) in variables))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 1
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False
    result=[next(c for j,c in enumerate(candidates) if solver.Value(variables[i,j])) for i,candidates in enumerate(candidate_lists)]
    return result, status == cp_model.OPTIMAL


def solve(snapshot: dict, unavailable: list[str] | None = None, *, allow_renewal: bool = False) -> dict[str, Any]:
    unavailable = sorted(set(unavailable or []))
    candidate_lists = options(snapshot, unavailable, allow_renewal)
    if cp_model:
        chosen, optimum_proven = _cp_sat(snapshot, candidate_lists)
    else:
        chosen = _exhaustive(snapshot, candidate_lists)
        optimum_proven = chosen is not None
    blockers = []
    for step, cands in zip(snapshot["steps"], candidate_lists):
        if not cands:
            blockers.append({"step_id":step["id"], "reason":"NO_ELIGIBLE_EXECUTOR",
                             "detail":f"No available, skilled employee has valid {step['permission']} access." if not allow_renewal else f"No available skilled employee has a renewable {step['permission']} grant."})
    if chosen is None and not blockers:
        blockers.append({"step_id":None, "reason":"POLICY_CONFLICT",
                         "detail":"Individually eligible candidates cannot satisfy separation-of-duties constraints together."})
    assignments = [{"step_id":s["id"], "step_name":s["name"],
                    "person_id":a["person_id"], "person_name":a["person_name"]}
                   for s,a in zip(snapshot["steps"], chosen or [])]
    renewals = sorted([{"person_id":pid, "permission":perm,
                        "type":"RENEW_EXPIRED_PERMISSION", "cost":1}
                       for pid,perm in {(a["person_id"],a["permission"]) for a in chosen or [] if a["renew"]}],
                      key=lambda x:(x["person_id"], x["permission"]))
    return {"feasible":chosen is not None, "assignments":assignments,
            "renewals":renewals, "blockers":blockers, "unavailable":unavailable,
            "mode":"repair-planning" if allow_renewal else "current-state",
            "solver":"CP-SAT" if cp_model else "exact-enumeration",
            "optimization_proven":optimum_proven}


def analyze(snapshot:dict, unavailable:list[str]) -> dict:
    baseline = solve(snapshot, unavailable)
    repaired = solve(snapshot, unavailable, allow_renewal=True) if not baseline["feasible"] else None
    baseline["repair"] = repaired if repaired and repaired["feasible"] and repaired["renewals"] else None
    if not baseline["feasible"] and baseline["repair"]:
        certainty = "minimal verified set" if baseline["repair"]["optimization_proven"] else "candidate set (optimality not proven)"
        baseline["explanation"] = f"Current access or duty separation blocks this workflow; renewing a {certainty} of existing expired grants could restore a policy-compliant assignment, subject to review."
    elif baseline["feasible"]:
        baseline["explanation"] = "A valid assignment exists with current access and separation-of-duties rules. This proves simulated assignment feasibility, not real-world execution."
    else:
        baseline["explanation"] = "No supported safe repair was found. Manual process, training, or staffing review is required; the system will not invent permissions."
    return baseline
