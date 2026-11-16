#!/usr/bin/env python3
"""Set the measured duration of matte-image in domains/presence-edit.jsonld from tests/evidence/matte_times.json (tools/measure/time_matte.py).
Like score, the one-time model load stays out of the per-image duration, because no action models it. A single portrait, so no start/end span.
Kept apart from set_durations.py, which asserts the planner reaches its whole load chain and stops with 'unreachable' on the current domain.
usage: tools/set_matte_duration.py     (rewrites the domain in place; run tests/test_actions.py after)"""
import json, math, os, statistics
def iso_s(x):
    """Seconds as a canonical ISO 8601 duration at millisecond resolution, the way the planner writes one: PT0.056S, PT1M7S."""
    ms = round(x * 1000); s, f = divmod(ms, 1000); h, r = divmod(s, 3600); m, sec = divmod(r, 60)
    out = "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "")
    if sec or f or (not h and not m): out += f"{sec}" + (("." + f"{f:03d}".rstrip("0")) if f else "") + "S"
    return out
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = f"{ROOT}/domains/presence-edit.jsonld"
m = json.load(open(f"{ROOT}/tests/evidence/matte_times.json"))["matte-image"]
warm = m["runs_s"][1:]; med = statistics.median(warm)
d = json.load(open(DOMAIN)); a = d["actions"]["matte-image"]
a["duration"] = iso_s(med)
a["duration_basis"] = (f"measured: warm median {round(med, 4)} s per image of {len(warm)} runs, to the millisecond; the cold first run took {m['runs_s'][0]} s. "
                       f"Excludes the one-time {m['model_load_s']} s model load, which no action models. One portrait ({m['input'][0]}x{m['input'][1]}), BiRefNet-matting at 1024, half precision")
a["measured"] = {"runs_s": m["runs_s"], "model_load_s": m["model_load_s"], "host": f"fedora, {m['device']}, torch {m['torch']}, tools/measure/time_matte.py, 2026-11-15"}
json.dump(d, open(DOMAIN, "w"), indent=1, ensure_ascii=False); open(DOMAIN, "a").write("\n")
print("matte-image", a["duration"])
