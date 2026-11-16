#!/usr/bin/env python3
"""Set measured durations in domains/presence-edit.jsonld from tests/evidence/{action_times,hair_times}.json (tools/measure/time_actions.py).
Each is the wall clock of `tools/aux.sh action <name>` on fedora (process start to exit, so interpreter and model start-up are inside it): the warm median of
runs 2..N, to the millisecond; run 1 is recorded as the cold run. usage: tools/set_action_durations.py, then tests/test_actions.py --update --only <names>."""
import json, os, statistics, platform
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOMAIN = f"{ROOT}/domains/presence-edit.jsonld"
def iso_s(x):
    ms = round(x * 1000); s, f = divmod(ms, 1000); h, r = divmod(s, 3600); m, sec = divmod(r, 60)
    out = "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "")
    if sec or f or (not h and not m): out += f"{sec}" + (("." + f"{f:03d}".rstrip("0")) if f else "") + "S"
    return out
d = json.load(open(DOMAIN)); done = []
for f in ("action_times", "hair_times"):
    for k, v in json.load(open(f"{ROOT}/tests/evidence/{f}.json")).items():
        r = v["runs_s"]; med = statistics.median(r[1:]); a = d["actions"][k]
        a["duration"] = iso_s(med)
        a["duration_basis"] = (f"measured: warm median {round(med, 3)} s of {len(r) - 1} runs, to the millisecond; the first run took {r[0]} s. Wall clock of tools/aux.sh action {k} "
                               f"on fedora, which includes process and model start-up")
        a["measured"] = {"runs_s": r, "host": f"{v['host']}, RTX 4090, tools/measure/time_actions.py, 2026-11-15"}; done.append((k, a["duration"]))
json.dump(d, open(DOMAIN, "w"), indent=1, ensure_ascii=False); open(DOMAIN, "a").write("\n"); print(done)
