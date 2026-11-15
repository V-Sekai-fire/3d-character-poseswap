#!/usr/bin/env python3
"""Planner unit test: every action of domains/presence-edit.jsonld gets a GOLDEN, a CONTROL and an INVARIANT.
The expected values come from the action's own text in the domain (preconditions, effects, duration), worked out here without the planner,
so a planner that returns anything else is caught. tests/golden/actions.json keeps the golden so a change to an action shows in review.

  GOLDEN     init = exactly the preconditions; task [action]  ->  plan is [action], start = origin, end = origin + duration, total = duration.
  CONTROL    (a) drop each precondition in turn: the planner must refuse.  (b) an action name that is not in the domain: the planner must refuse.
             A control that passes means the golden proves nothing.
  INVARIANT  (a) two runs give identical bytes.  (b) [action, action] succeeds, so the action does not clear its own preconditions; the total is between 1 x and 2 x the
             duration because the planner overlaps independent steps (no resource constraint in the domain: see docs/aux-route.md).
             (c) the duration is ISO 8601, and a marker (PT0S) only for composite markers; duration_basis starts with measured or estimate or says composite.
  COMMAND    DRY_RUN=1 tools/aux.sh action <name>: exit code and the printed command match the golden; an unknown action exits 64;
             the dry run writes nothing except the out/ folder.

usage: tests/test_actions.py [--update] [--only name,...]     env PERSONA_PLAN = planner binary
"""
import json, os, re, subprocess, sys, tempfile, copy, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = f"{ROOT}/domains/presence-edit.jsonld"; BASE = f"{ROOT}/problems/aux-route-ready.jsonld"; GOLD = f"{ROOT}/tests/golden/actions.json"
PLANNER = os.environ.get("PERSONA_PLAN") or f"{ROOT}/.planner/.lake/build/bin/persona_plan"
ISO = re.compile(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$")

def secs(iso):
    m = ISO.match(iso); assert m and iso != "P" and not iso.endswith("T"), f"not an ISO 8601 duration: {iso!r}"
    d, h, mi, s = (float(x) if x else 0.0 for x in m.groups()); return d * 86400 + h * 3600 + mi * 60 + s
def stamp(t): return dt.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)

domain = json.load(open(DOMAIN)); base = json.load(open(BASE)); ORIGIN = base["origin"]
def spec(name):
    a = domain["actions"][name]; pre, eff, other = [], [], []
    for b in a["body"]:
        if "eval" in b and b["eval"].get("type") == "pointer/ge": pre.append((b["eval"]["pointer"], b["eval"]["value"]))
        elif "pointer/set" in b: eff.append((b["pointer"] if "pointer" in b else b["pointer/set"], b["value"]))
        else: other.append(b)
    return pre, eff, other, a.get("duration"), a.get("duration_basis", "")

def problem(true_ptrs, tasks):
    p = copy.deepcopy(base); p["todo_list"] = tasks
    for v in p["variables"]:
        for k in v["init"]: v["init"][k] = 0
    for ptr, val in true_ptrs:
        _, grp, key = ptr.split("/"); g = next(v for v in p["variables"] if v["name"] == grp); g["init"][key] = val
    return p

def plan(p, dom=None):
    with tempfile.TemporaryDirectory() as d:
        pf, of = f"{d}/p.json", f"{d}/o.json"; json.dump(p, open(pf, "w")); df = DOMAIN
        if dom is not None: df = f"{d}/d.json"; json.dump(dom, open(df, "w"))
        r = subprocess.run([PLANNER, df, pf, of], capture_output=True, text=True)
        raw = open(of).read() if os.path.exists(of) else ""
    return r.returncode, raw, (json.loads(raw) if raw.strip().startswith("{") else {})

def run_tests(only=None, update=False):
    gold = {} if update or not os.path.exists(GOLD) else json.load(open(GOLD)); new = {}; results = []
    def check(ok, label): results.append((ok, label)); print(("PASS  " if ok else "FAIL  ") + label)
    for name in [n for n in domain["actions"] if not only or n in only]:
        pre, eff, other, dur, basis = spec(name); g = {"preconditions": [p for p, _ in pre], "effects": [p for p, _ in eff]}
        check(not other and eff, f"{name}: the action is made only of ge-preconditions and sets (a form this test does not know would be skipped silently)")
        if other: continue
        # --- invariant (c): duration text
        n = 0.0
        try: n = secs(dur); okd = True
        except Exception: okd = False
        check(okd and (n > 0 or "composite" in basis), f"{name}: INVARIANT duration {dur} is ISO 8601" + ("" if n else " (composite marker)"))
        check(bool(re.match(r"^(measured|estimate|composite)", basis)), f"{name}: INVARIANT duration_basis says measured, estimate or composite")
        # --- golden
        rc, raw, out = plan(problem(pre, [[name]]))
        steps = [s["action"] for s in out.get("steps", [])]; ok = rc == 0 and not out.get("refused") and steps == [name]
        if ok:
            s = out["steps"][0]; exp_end = stamp(ORIGIN) + dt.timedelta(seconds=n)
            ok = (s["start"] == ORIGIN and stamp(s["end"]) == exp_end and abs(secs(s["duration"]) - n) < 1e-6 and abs(secs(out["temporal"]["total"]) - n) < 1e-6 and out["temporal"]["consistent"])
        check(ok, f"{name}: GOLDEN plan is [{name}], starts at the origin, lasts {dur}, total {dur}")
        g["plan"] = [name]; g["duration"] = dur; g["total"] = dur
        # --- control (a): each precondition removed in turn
        for drop in range(len(pre)):
            rc2, raw2, out2 = plan(problem(pre[:drop] + pre[drop + 1:], [[name]]))
            check(rc2 != 0 or bool(out2.get("refused")) or [s["action"] for s in out2.get("steps", [])] != [name], f"{name}: CONTROL without {pre[drop][0]} the planner refuses")
        # --- control (b): a name that is not an action
        rc3, raw3, out3 = plan(problem(pre, [[name + "-no-such"]]))
        check(rc3 != 0 or bool(out3.get("refused")) or not out3.get("steps"), f"{name}: CONTROL an unknown action name is refused")
        # --- invariant (a): determinism, (b): twice
        check(plan(problem(pre, [[name]]))[1] == raw, f"{name}: INVARIANT two runs give identical bytes")
        rc4, raw4, out4 = plan(problem(pre, [[name], [name]]))
        s4 = [s["action"] for s in out4.get("steps", [])]
        check(rc4 == 0 and s4 == [name, name] and n - 1e-6 <= secs(out4["temporal"]["total"]) <= 2 * n + 1e-6, f"{name}: INVARIANT twice in a row succeeds (it keeps its own preconditions) and totals between 1 x and 2 x {dur}")
        g["twice_total"] = out4.get("temporal", {}).get("total")
        # --- command (dry run)
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, DRY_RUN="1", OUT=f"{d}/out", SOURCE="SRC", UNIT="cm", LABELLED="LAB", PERSONA_PLAN=PLANNER)
            before = sorted(os.listdir(d)); r = subprocess.run(["bash", f"{ROOT}/tools/aux.sh", "action", name], capture_output=True, text=True, env=env, cwd=ROOT)
            after = sorted(os.listdir(d)); cmd = (r.stdout + r.stderr).replace(d, "$OUT_DIR").replace(ROOT, "$REPO").replace(os.path.expanduser("~"), "$HOME").strip()
            r2 = subprocess.run(["bash", f"{ROOT}/tools/aux.sh", "action", name + "-no-such"], capture_output=True, text=True, env=env, cwd=ROOT)
        g["command"] = {"rc": r.returncode, "out": cmd}
        check(set(after) - set(before) <= {"out"}, f"{name}: INVARIANT the dry run writes nothing except out/")
        check(r2.returncode == 64, f"{name}: CONTROL an unknown action name exits 64 (got {r2.returncode})")
        if not update and name in gold: check(gold[name] == g, f"{name}: GOLDEN file tests/golden/actions.json still equals the oracle and the dry-run command")
        new[name] = g
    if update:
        os.makedirs(os.path.dirname(GOLD), exist_ok=True); merged: dict = json.load(open(GOLD)) if os.path.exists(GOLD) and only else {}
        merged.update(new); json.dump(merged, open(GOLD, "w"), indent=1, sort_keys=True); open(GOLD, "a").write("\n"); print(f"golden written: {len(merged)} actions")
    # ---- ranges: actions timed over several runs carry duration (typical), start (release) and end (deadline) = a span the planner checks
    ev_path = f"{ROOT}/tests/evidence/load_times.json"
    if not only and os.path.exists(ev_path):
        ev = json.load(open(ev_path)); grp = list(ev); a = domain["actions"]
        iso = lambda x: "PT" + (f"{x // 3600}H" if x >= 3600 else "") + (f"{x % 3600 // 60}M" if x % 3600 >= 60 else "") + (f"{x % 60}S" if x % 60 or x == 0 else "")
        pre = {b["eval"]["pointer"] for k in grp for b in a[k]["body"] if "eval" in b} - {b["pointer/set"] for k in grp for b in a[k]["body"] if "pointer/set" in b}
        def group(durs):
            dd = copy.deepcopy(domain)
            for k, x in durs.items(): dd["actions"][k]["duration"] = iso(x)
            return plan(problem([(q, 1) for q in pre], [[k] for k in grp]), dd)[2]
        def ends(out):
            f = {}
            for st in out["steps"]: f.setdefault(st["action"], st)
            return {k: int((stamp(v["end"]) - stamp(ORIGIN)).total_seconds()) for k, v in f.items()}
        import math, statistics
        nom = {k: math.ceil(statistics.median(v["runs"][1:])) for k, v in ev.items()}; slow = {k: math.ceil(max(v["runs"])) for k, v in ev.items()}; fast = {k: math.ceil(min(v["runs"])) for k, v in ev.items()}
        for k in grp:
            check(a[k]["measured"]["runs_s"] == ev[k]["runs"], f"{k}: RANGE GOLDEN the runs in the domain are the runs in tests/evidence/load_times.json")
            check(secs(a[k]["duration"]) == nom[k], f"{k}: RANGE GOLDEN duration {a[k]['duration']} is the warm median ({statistics.median(ev[k]['runs'][1:])} s) rounded up")
            check(secs(a[k]["duration"]) >= statistics.median(ev[k]["runs"][1:]) and secs(a[k]["duration"]) <= slow[k], f"{k}: RANGE INVARIANT the typical duration lies inside the measured range")
            check(a[k]["start"] == ORIGIN, f"{k}: RANGE GOLDEN the span starts at the origin (the release time)")
        out_slow = group(slow); dead = ends(out_slow)
        for k in grp: check(int((stamp(a[k]["end"]) - stamp(ORIGIN)).total_seconds()) == dead[k], f"{k}: RANGE GOLDEN the deadline {a[k]['end']} is the earliest end when every action takes its slowest run ({dead[k]} s)")
        o_nom, o_fast = group(nom), group(fast)
        check(group({})["temporal"]["consistent"] and o_nom["temporal"]["consistent"] and o_fast["temporal"]["consistent"] and out_slow["temporal"]["consistent"], "RANGE INVARIANT the group is consistent at the typical, the fastest and the slowest run")
        tf, tn, ts = (secs(o["temporal"]["total"]) for o in (o_fast, o_nom, out_slow)); check(tf <= tn <= ts, f"RANGE INVARIANT the group total grows with the durations: fastest {tf:g} s <= typical {tn:g} s <= slowest {ts:g} s")
        for k in grp:
            late = dict(slow); late[k] = slow[k] + 1; o = group(late)
            check(o.get("temporal", {}).get("consistent") is False, f"{k}: RANGE CONTROL one second slower than its slowest measured run makes the plan inconsistent")
        check(sum(statistics.median(v["runs"][1:]) for v in ev.values()) <= 7.0 + 0.5, "RANGE INVARIANT the five warm medians add to no more than the 7.0 s the whole load took in baseline.log (+0.5 s)")
        sec = float(open(f"{ROOT}/tests/evidence/baseline_log_lines.txt").read().split("EDIT-OK")[1].split("seconds=")[1].split()[0])
        check(secs(a["edit"]["duration"]) == math.ceil(sec), f"edit: GOLDEN duration {a['edit']['duration']} is the {sec} s logged in baseline.log, rounded up")
    bad = [l for ok, l in results if not ok]; print(f"---- {len(results) - len(bad)} passed, {len(bad)} failed, {len(new)} actions")
    return 1 if bad else 0

if __name__ == "__main__":
    only = None
    if "--only" in sys.argv: only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    sys.exit(run_tests(only, "--update" in sys.argv))
