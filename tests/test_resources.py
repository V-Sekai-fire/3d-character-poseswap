#!/usr/bin/env python3
"""The one GPU, with only what the domain already has: every GPU action reads /input/gpu and sets it back, so the planner puts GPU steps one after another.
  GOLDEN     OmniGen2 load group: the four GPU steps run one after another, 10 s (4+4+1+1); AUX route 5461 s.
  CONTROL    a desk that states no GPU (/input/gpu 0) is refused; with the read and set removed from the GPU actions the same group overlaps and the total falls to 5 s.
  INVARIANT  no two GPU steps overlap in the plan, and every GPU action reads and sets /input/gpu.
usage: tests/test_resources.py   env PERSONA_PLAN = planner binary"""
import json, os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import test_actions as T
R = []; ck = lambda ok, m: (R.append(ok), print(("PASS  " if ok else "FAIL  ") + m))
a = T.domain["actions"]; GPU = [k for k, v in a.items() if any(b.get("eval", {}).get("pointer") == "/input/gpu" for b in v["body"])]
secs = lambda iso: sum(float(x) * m for x, m in zip(__import__("re").findall(r"[\d.]+", iso), ({"H": 3600, "M": 60, "S": 1}[c] for c in __import__("re").findall(r"[HMS]", iso))))
names = ["load-qwen25vl-conditioner", "load-omnigen2-transformer", "load-omnigen2-vae", "load-editscore-lora", "merge-editscore-lora"]
def pre(d, extra=()):
    ac = d["actions"]; reads = {b["eval"]["pointer"] for k in names for b in ac[k]["body"] if "eval" in b}; sets = {b["pointer/set"] for k in names for b in ac[k]["body"] if "pointer/set" in b}
    return sorted((reads - sets) | set(extra))
def group(d=None, gpu=1):
    dd = d or T.domain; return T.plan(T.problem([(q, gpu if q == "/input/gpu" else 1) for q in pre(dd, ["/input/gpu"])], [[k] for k in names]), d)[2]
def route(gpu):
    p = json.load(open(T.BASE)); [v["init"].__setitem__("gpu", gpu) for v in p["variables"] if v["name"] == "input"]; p["todo_list"] = [{"goal": [{"pointer": "/aux/rigged", "eq": 1}]}]; return T.plan(p, None)[2]
g = group(); ck(secs(g["temporal"]["total"]) == 10, f"load group GOLDEN total {g['temporal']['total']} = 4+4+1+1 s: the GPU steps one after another")
r = route(1); ck(r["temporal"]["total"] == "PT1H31M1S", f"AUX route GOLDEN total {r['temporal']['total']}")
ck(route(0).get("refused") == "unreachable", "desk without a GPU CONTROL the AUX route is refused as unreachable")
d = copy.deepcopy(T.domain)
for k in GPU: d["actions"][k]["body"] = [b for b in d["actions"][k]["body"] if b.get("pointer/set") != "/input/gpu" and b.get("eval", {}).get("pointer") != "/input/gpu"]
u = group(d); ck(secs(u["temporal"]["total"]) == 5, f"load group CONTROL without the read and set the loads overlap: total {u['temporal']['total']} (5 s)")
first = {}
for st in g["steps"]: first.setdefault(st["action"], st)
w = sorted((s["start"], s["end"]) for k, s in first.items() if k in GPU); ck(all(w[i][1] <= w[i + 1][0] for i in range(len(w) - 1)), f"INVARIANT no two GPU steps overlap ({len(w)} GPU steps in the load group)")
ck(len(GPU) == 9 and all(any(b.get("pointer/set") == "/input/gpu" for b in a[k]["body"]) for k in GPU), "INVARIANT all 9 GPU actions read and set /input/gpu")
print(f"---- {sum(R)} passed, {len(R) - sum(R)} failed"); sys.exit(0 if all(R) else 1)
