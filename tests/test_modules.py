#!/usr/bin/env python3
"""The six module files and domains/presence-edit.jsonld describe one domain. Nothing generates one from the other, so they can drift: this test keeps them honest.
  GOLDEN     both desks' plans from the modules, composed by persona_plan in aux.sh's order, equal the plans from the single file (action, start and end of every step).
  CONTROL    a module with one action's duration changed gives a different plan, so the comparison can see a difference.
  INVARIANT  every action and method of the single file is in exactly one module, and the modules hold nothing the single file lacks.
usage: tests/test_modules.py   env PERSONA_PLAN = planner binary"""
import json, os, subprocess, sys, tempfile, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT); PLAN = os.environ.get("PERSONA_PLAN", ".planner/.lake/build/bin/persona_plan")
MODS = re.search(r"^MODS=\((.*)\)", open("tools/aux.sh").read(), re.M).group(1).split()
R = []; ck = lambda ok, m: (R.append(ok), print(("PASS  " if ok else "FAIL  ") + m))
def plan(domain, problem, goal="/aux/rigged"):
    p = json.load(open(problem)); p["todo_list"] = [{"goal": [{"pointer": goal, "eq": 1}]}]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonld", delete=False) as f: json.dump(p, f); pf = f.name
    out = subprocess.run([PLAN, domain, pf], capture_output=True, text=True).stdout; os.unlink(pf)
    d = json.loads(out); return d.get("refused") or [(s["action"], s["start"], s["end"]) for s in d["steps"]]
files = [f"domains/modules/{m}.jsonld" for m in MODS]; mods = [json.load(open(f)) for f in files]; whole = json.load(open("domains/presence-edit.jsonld"))
for pb in ("problems/aux-route-ready.jsonld", "problems/aux-route-2026-11-15.jsonld"):
    a, b = plan("domains/presence-edit.jsonld", pb), plan(",".join(files), pb)
    ck(a == b and not isinstance(a, str), f"{os.path.basename(pb)} GOLDEN the modules plan the same as the single file ({len(a)} steps)")
tampered = json.loads(json.dumps(mods[MODS.index("aux-motion")])); tampered["actions"]["build-warp"]["duration"] = "PT2H"
with tempfile.NamedTemporaryFile("w", suffix=".jsonld", delete=False) as f: json.dump(tampered, f); tf = f.name
t = [tf if m == "aux-motion" else f for m, f in zip(MODS, files)]
ck(plan(",".join(t), "problems/aux-route-ready.jsonld") != plan("domains/presence-edit.jsonld", "problems/aux-route-ready.jsonld"), "CONTROL a changed duration in one module is seen")
os.unlink(tf)
for kind in ("actions", "methods"):
    owner = {}
    for m, d in zip(MODS, mods):
        for k in d[kind]: owner.setdefault(k, []).append(m)
    ck(set(owner) == set(whole[kind]) and all(len(v) == 1 for v in owner.values()), f"INVARIANT every {kind[:-1]} is in exactly one module ({len(whole[kind])})")
    same = all(json.dumps(d[kind][k], sort_keys=True) == json.dumps(whole[kind][k], sort_keys=True) for d in mods for k in d[kind] if k in whole[kind])
    ck(same, f"INVARIANT each {kind[:-1]} reads the same in its module and in the single file")
print(f"---- {sum(R)} passed, {len(R) - sum(R)} failed"); sys.exit(0 if all(R) else 1)
