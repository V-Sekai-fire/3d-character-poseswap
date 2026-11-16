#!/usr/bin/env python3
"""Set measured durations in domains/presence-edit.jsonld from tests/evidence/, as spans the planner already understands.

For an action timed over several runs:
  duration  the typical length, the warm median, exact to the millisecond (the planner counts milliseconds)
  start     the release time: the problem origin (the earliest it may begin)
  end       the deadline: the earliest end the plan gives when EVERY ranged action takes its slowest measured run (the cold one).
            The planner calls a plan consistent only while each step ends by its deadline, so any run inside the measured range is consistent and one slower than the
            slowest measured run is not.
  measured  the raw runs in seconds, the host and the command, kept for the tests (the planner ignores the key).
For an action with one logged sample the duration is that sample, with no range.
usage: tools/set_durations.py            (rewrites the domain in place; run tests/test_actions.py after)"""
import json, math, os, statistics, subprocess, sys, tempfile, copy, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = f"{ROOT}/domains/presence-edit.jsonld"; PROBLEM = f"{ROOT}/problems/aux-route-ready.jsonld"
PLANNER = os.environ.get("PERSONA_PLAN") or f"{ROOT}/.planner/.lake/build/bin/persona_plan"
ev = json.load(open(f"{ROOT}/tests/evidence/load_times.json")); sc = json.load(open(f"{ROOT}/tests/evidence/score_times.json"))["score"]; base_lines = open(f"{ROOT}/tests/evidence/baseline_log_lines.txt").read()
d = json.load(open(DOMAIN)); prob = json.load(open(PROBLEM)); ORIGIN = prob["origin"]
def iso_s(x):
    """Seconds as a canonical ISO 8601 duration at millisecond resolution, the way the planner writes one: PT0.056S, PT1M7S."""
    ms = round(x * 1000); s, f = divmod(ms, 1000); h, r = divmod(s, 3600); m, sec = divmod(r, 60)
    out = "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "")
    if sec or f or (not h and not m): out += f"{sec}" + (("." + f"{f:03d}".rstrip("0")) if f else "") + "S"
    return out
iso = iso_s
def stamp(s):
    t = dt.datetime.strptime(ORIGIN, "%Y-%m-%dT%H:%M:%SZ") + dt.timedelta(milliseconds=round(s * 1000))
    return t.strftime("%Y-%m-%dT%H:%M:%S") + (f".{t.microsecond // 1000:03d}" if t.microsecond else "") + "Z"
parse_stamp = lambda t: dt.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ" if "." in t else "%Y-%m-%dT%H:%M:%SZ")
LOADS = list(ev); GROUP = LOADS + ["score"]; CHAIN = LOADS + ["edit", "score"]   # score runs behind edit, which runs behind the loads
ev["score"] = {"runs": sc["runs"], "cold": max(sc["runs"]), "warm_median": statistics.median(sc["runs"])}   # every run is warm: the judge was loaded once
HOST = "fedora, RTX 4090, driver 615.71.09, BF16 base weights, 5 runs, the first cold from disk (tools/measure/time_loads.py, 2026-11-15)"
nominal = {k: round(v["warm_median"], 3) for k, v in ev.items()}; slowest = {k: round(max(v["runs"]), 3) for k, v in ev.items()}   # exact to the millisecond, never rounded up
edit_s = round(float(base_lines.split("EDIT-OK")[1].split("seconds=")[1].split()[0]), 3)

def plan_with(durs):
    dd = copy.deepcopy(d)
    for k, s in durs.items(): dd["actions"][k]["duration"] = iso(s); dd["actions"][k].pop("start", None); dd["actions"][k].pop("end", None)
    dd["actions"]["edit"]["duration"] = iso(edit_s)
    pre = [b["eval"]["pointer"] for k in CHAIN for b in d["actions"][k]["body"] if "eval" in b]; eff = [b["pointer/set"] for k in CHAIN for b in d["actions"][k]["body"] if "pointer/set" in b]
    p = copy.deepcopy(prob); p["todo_list"] = [[k] for k in CHAIN]
    for v in p["variables"]:
        for k in v["init"]: v["init"][k] = 0
    for ptr in (set(pre) - set(eff)) | {"/input/gpu"}:   # the desk states its GPU; every GPU action reads it and gives it back
        _, grp, key = ptr.split("/"); next(v for v in p["variables"] if v["name"] == grp)["init"][key] = 1
    with tempfile.TemporaryDirectory() as t:
        json.dump(dd, open(f"{t}/d.json", "w")); json.dump(p, open(f"{t}/p.json", "w")); subprocess.run([PLANNER, f"{t}/d.json", f"{t}/p.json", f"{t}/o.json"], check=True, capture_output=True)
        out = json.load(open(f"{t}/o.json"))
    assert not out.get("refused"), out
    first = {}
    for s in out["steps"]: first.setdefault(s["action"], s)
    o = parse_stamp(ORIGIN)
    return {k: round((parse_stamp(s["end"]) - o).total_seconds(), 3) for k, s in first.items()}

deadline = plan_with(slowest)          # earliest end of each step when every action takes its slowest run
for k in GROUP:
    a = d["actions"][k]; v = ev[k]
    a["duration"] = iso(nominal[k]); a["start"] = ORIGIN; a["end"] = stamp(deadline[k])
    if k == "score":
        a["duration_basis"] = (f"measured: median {v['warm_median']} s per edit over {len(v['runs'])} edits (K=4 passes of the Qwen3-VL-8B judge), exact to the millisecond; slowest {max(v['runs'])} s. "
                               f"Excludes the one-time {sc['judge_load_and_smoke_s']} s judge load and smoke test, which no action models. end is the deadline when the loads, edit and score all take their slowest run")
        a["measured"] = {"runs_s": sc["runs"], "judge_load_and_smoke_s": sc["judge_load_and_smoke_s"], "host": sc["host"]}
    else:
        a["duration_basis"] = (f"measured: warm median {v['warm_median']} s of {len(v['runs']) - 1} runs, exact to the millisecond; slowest run {max(v['runs'])} s (cold). "
                               f"start is the release time and end the deadline if every action in the chain takes its slowest run, so the span covers every run measured")
        a["measured"] = {"runs_s": v["runs"], "cold_s": v["cold"], "warm_median_s": v["warm_median"], "host": HOST}
sec = float(base_lines.split("EDIT-OK")[1].split("seconds=")[1].split()[0])
e = d["actions"]["edit"]; e["duration"] = iso(round(sec, 3))
e["duration_basis"] = f"measured once: {sec} s for one 50-step BF16 edit at 672x1024 with the LoRA (baseline.log, fedora RTX 4090), exact to the millisecond; a single sample, so no range"
e["measured"] = {"runs_s": [sec], "host": "fedora, RTX 4090 (baseline.log, one run)"}
json.dump(d, open(DOMAIN, "w"), indent=1, ensure_ascii=False); open(DOMAIN, "a").write("\n")
print({k: (d["actions"][k]["duration"], d["actions"][k]["end"][11:19]) for k in GROUP}, "| edit", e["duration"])
