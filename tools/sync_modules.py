#!/usr/bin/env python3
"""Copy every action and method of the single domain file (domains/presence-edit.jsonld) into the module that owns it, so the modules read the same as the single file.
tests/test_modules.py asserts that. Run it after a script edits the single file (set_durations.py, set_matte_duration.py, set_action_durations.py).
usage: tools/sync_modules.py"""
import glob, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
whole = json.load(open(f"{ROOT}/domains/presence-edit.jsonld")); changed = 0
for f in sorted(glob.glob(f"{ROOT}/domains/modules/*.jsonld")):
    d = json.load(open(f)); before = json.dumps(d, sort_keys=True)
    for kind in ("actions", "methods"):
        for k in d.get(kind, {}): d[kind][k] = whole[kind][k]
    if json.dumps(d, sort_keys=True) != before:
        json.dump(d, open(f, "w"), indent=1, ensure_ascii=False); open(f, "a").write("\n"); changed += 1; print("updated", os.path.basename(f))
print(changed, "modules changed")
