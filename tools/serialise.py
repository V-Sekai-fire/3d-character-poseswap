#!/usr/bin/env python3
"""Serialise the steps of a plan that share a resource (the one GPU), keeping every dependency the planner already enforces.

The planner has no resource model: independent steps overlap, so its total is a lower bound while two GPU steps cannot run at once on one card.
An action marks the resource it holds with `"resource": "gpu"` in the domain (the planner ignores the key).
Steps are taken in the planner's order. A step starts when it is released, when every earlier step that sets a fact it needs has ended,
and, if it holds a resource, when the previous step holding that resource has ended.

usage: serialise.py <domain.jsonld> <plan.json> [--json]      prints the serial total, the planner's total, and each step's window
"""
import json, sys, datetime as dt, re

def secs(iso):
    m = re.match(r"^PT?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$", iso.replace("P", "PT", 1) if not iso.startswith("PT") else iso)
    assert m, f"not a duration: {iso!r}"
    h, mi, s = (float(x) if x else 0.0 for x in m.groups()); return h * 3600 + mi * 60 + s

def serialise(domain, plan):
    acts = domain["actions"]
    first = []; seen = set()
    for st in plan["steps"]:
        if st["action"] not in seen: seen.add(st["action"]); first.append(st)       # the first row of a step is its earliest window; later rows are its latest
    def needs(a): return {b["eval"]["pointer"] for b in acts[a]["body"] if "eval" in b}
    def sets(a): return {b["pointer/set"] for b in acts[a]["body"] if "pointer/set" in b}
    out = []; free = {}
    for st in first:
        a = st["action"]; d = secs(st["duration"]);
        start = 0
        for prev in out:
            if sets(prev["action"]) & needs(a): start = max(start, prev["end"])
        res = acts[a].get("resource")
        if res: start = max(start, free.get(res, 0))
        end = start + d; out.append({"action": a, "start": start, "end": end, "resource": res}); 
        if res: free[res] = end
    return out, max([o["end"] for o in out] or [0])

if __name__ == "__main__":
    domain = json.load(open(sys.argv[1])); plan = json.load(open(sys.argv[2])); rows, total = serialise(domain, plan)
    if "--json" in sys.argv: print(json.dumps({"serial_total_s": total, "planner_total_s": secs(plan["temporal"]["total"]), "steps": rows})); sys.exit(0)
    print(f"serial total {total:g} s | planner total {secs(plan['temporal']['total']):g} s (a lower bound: it lets steps share a resource)")
    for r in rows: print(f"  {r['start']:6g} {r['end']:6g}  {r['action']}" + (f"  [{r['resource']}]" if r["resource"] else ""))
