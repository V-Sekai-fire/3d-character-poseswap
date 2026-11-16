"""Time the AUX command actions of tools/aux.sh, N runs each on this machine, wall clock around the whole action (process start to exit).
Run 1 is the cold one (nothing cached); the domain's duration is the warm median of the rest. Exits non-zero when any run fails.
usage: RUNS=6 SOURCE=<mesh> LABELLED=<glb> tools/measure/time_actions.py <checkout-with-inputs> action... > tests/evidence/action_times.json"""
import json, os, subprocess, sys, time, platform
root, acts, N = sys.argv[1], sys.argv[2:], int(os.environ.get("RUNS", "6"))
res = {}
for a in acts:
    runs = []
    for i in range(N):
        t = time.perf_counter(); r = subprocess.run(["bash", "tools/aux.sh", "action", a], cwd=root, capture_output=True, text=True); runs.append(round(time.perf_counter() - t, 3))
        if r.returncode: sys.exit(f"{a} run {i+1} rc={r.returncode}: {(r.stdout+r.stderr)[-400:]}")
    res[a] = {"runs_s": runs, "host": platform.node()}
print(json.dumps(res, indent=1))
