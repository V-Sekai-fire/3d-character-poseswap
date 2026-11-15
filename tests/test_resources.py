#!/usr/bin/env python3
"""Tests for tools/serialise.py: steps that hold the same resource (the one GPU) never overlap, and the dependencies the planner enforces still hold.

  GOLDEN     AUX route: the serial total equals the planner total (its GPU steps are already ordered by what they need): 5461 s.
             OmniGen2 load group (4 + 4 + 1 + 1 s, three of them on the GPU): the planner overlaps the loads, the serial total is the sum of the GPU steps on the one card.
  CONTROL    with the `resource` marks removed the serial total falls back to the planner's, so the marks are what change the answer;
             two GPU steps that the planner overlaps are found overlapping in the planner's own schedule (the fault the tool exists to remove).
  INVARIANT  serial total >= planner total; no two steps with the same resource overlap; a step never starts before a step that sets a fact it needs has ended.
usage: tests/test_resources.py       env PERSONA_PLAN = planner binary"""
import json, os, sys, copy, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import test_actions as T, serialise as S

results = []
def check(ok, label): results.append(ok); print(("PASS  " if ok else "FAIL  ") + label)
domain = T.domain; acts = domain["actions"]
needs = lambda a: {b["eval"]["pointer"] for b in acts[a]["body"] if "eval" in b}; sets = lambda a: {b["pointer/set"] for b in acts[a]["body"] if "pointer/set" in b}

def route(dom=None):
    p = json.load(open(T.BASE)); p["todo_list"] = [{"goal": [{"pointer": "/aux/rigged", "eq": 1}]}]
    return T.plan(p, dom)[2]
def group(dom=None):
    names = ["load-qwen25vl-conditioner", "load-omnigen2-transformer", "load-omnigen2-vae", "load-editscore-lora", "merge-editscore-lora"]
    pre = {q for k in names for q in needs(k)} - {q for k in names for q in sets(k)}
    return T.plan(T.problem([(q, 1) for q in pre], [[k] for k in names]), dom)[2]
def overlap_in_planner(plan, dom):
    first = {}
    for st in plan["steps"]: first.setdefault(st["action"], st)
    g = [(st["start"], st["end"], a) for a, st in first.items() if dom["actions"][a].get("resource") == "gpu"]
    return [(a, b) for i, (s1, e1, a) in enumerate(g) for (s2, e2, b) in g[i + 1:] if s1 < e2 and s2 < e1]
def unmarked():
    d = copy.deepcopy(domain)
    for a in d["actions"].values(): a.pop("resource", None)
    return d

r = route(); rows, total = S.serialise(domain, r); pt = S.secs(r["temporal"]["total"])
check(total == 5461 and pt == 5461, f"AUX route GOLDEN serial total {total:g} s equals the planner total {pt:g} s (PT1H31M1S)")
check(not overlap_in_planner(r, domain), "AUX route GOLDEN no two GPU steps overlap in the planner's own schedule")
g = group(); rows_g, tot_g = S.serialise(domain, g); ptg = S.secs(g["temporal"]["total"])
gpu_sum = sum(S.secs(acts[k]["duration"]) for k in ("load-qwen25vl-conditioner", "load-omnigen2-transformer", "load-omnigen2-vae", "merge-editscore-lora"))
check(ptg == 5 and tot_g == gpu_sum == 10, f"load group GOLDEN planner total {ptg:g} s, serial total {tot_g:g} s = the four GPU steps one after another ({gpu_sum:g} s)")
ov = overlap_in_planner(g, domain)
check(len(ov) >= 2, f"load group CONTROL the planner alone overlaps GPU steps ({len(ov)} pairs, e.g. {ov[0] if ov else None}): the fault the serialiser removes")
rows_u, tot_u = S.serialise(unmarked(), g); check(tot_u == ptg, f"load group CONTROL without the resource marks the serial total falls back to the planner's ({tot_u:g} s)")
for name, rr, tot, pl in (("AUX route", rows, total, pt), ("load group", rows_g, tot_g, ptg)):
    check(tot >= pl, f"{name} INVARIANT serial total {tot:g} s >= planner total {pl:g} s")
    gp = [x for x in rr if x["resource"] == "gpu"]; ok = all(not (a["start"] < b["end"] and b["start"] < a["end"]) for i, a in enumerate(gp) for b in gp[i + 1:])
    check(ok, f"{name} INVARIANT no two GPU steps overlap after serialising ({len(gp)} GPU steps)")
    bad = [(b["action"], a["action"]) for i, a in enumerate(rr) for b in rr[i + 1:] if sets(a["action"]) & needs(b["action"]) and b["start"] < a["end"]]
    check(not bad, f"{name} INVARIANT every step starts after the steps that set what it needs have ended")
print(f"---- {sum(results)} passed, {len(results) - sum(results)} failed"); sys.exit(0 if all(results) else 1)
