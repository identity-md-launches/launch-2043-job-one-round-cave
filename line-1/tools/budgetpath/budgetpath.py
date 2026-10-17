#!/usr/bin/env python3
"""Compute a deterministic critical path for a small offline task plan."""
import argparse, json, sys

def read_plan(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a non-empty list")
    out = {}
    for item in tasks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("each task needs a string id")
        ident = item["id"]
        if ident in out or ident == "":
            raise ValueError("task ids must be unique and non-empty")
        duration = item.get("minutes")
        if type(duration) is not int or duration < 0:
            raise ValueError("minutes must be a non-negative integer")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            raise ValueError("depends_on must be a list of task ids")
        out[ident] = {"minutes": duration, "depends_on": deps}
    for ident, item in out.items():
        if ident in item["depends_on"] or any(dep not in out for dep in item["depends_on"]):
            raise ValueError("unknown dependency or self-dependency in " + ident)
    return out, data.get("budget_minutes")

def solve(tasks, budget):
    state, finish, path = {}, {}, {}
    def visit(ident):
        if state.get(ident) == 1: raise ValueError("dependency cycle")
        if state.get(ident) == 2: return finish[ident]
        state[ident] = 1
        preds = tasks[ident]["depends_on"]
        best = max((visit(dep) for dep in preds), default=0)
        chosen = max(preds, key=lambda dep: (finish[dep], dep), default=None)
        finish[ident] = best + tasks[ident]["minutes"]
        path[ident] = (path[chosen] + [ident]) if chosen else [ident]
        state[ident] = 2
        return finish[ident]
    for ident in tasks: visit(ident)
    end = max(tasks, key=lambda ident: (finish[ident], ident))
    total = finish[end]
    return {"total_minutes": total, "critical_path": path[end],
            "within_budget": budget is None or total <= budget,
            "budget_minutes": budget}

def main():
    ap = argparse.ArgumentParser(description="check a bounded task plan's critical path")
    ap.add_argument("plan", nargs="?", default="example.json")
    args = ap.parse_args()
    try:
        tasks, budget = read_plan(args.plan)
        print(json.dumps(solve(tasks, budget), indent=2, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("budgetpath: " + str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
