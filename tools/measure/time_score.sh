set -u
cd /home/setup/og2 || exit 1
rm -rf /tmp/ps_time; mkdir -p /tmp/ps_time/set
python3 - <<'E'
import json, os, shutil
T = json.load(open("/home/setup/og2/tasks.json")); src = "/home/setup/og2/edits/bf16-lora"; files = sorted(os.listdir(src))
print("tasks", len(T), "keys", list(T[0])[:6] if isinstance(T, list) else list(T)[:3]); print("files", len(files), files[:2])
ids = [t["id"] for t in T]; pick = []
for t in T:
    m = [f for f in files if t["id"] in f]
    if m: pick.append((t, m[0]))
    if len(pick) == 6: break
json.dump([t for t, _ in pick], open("/tmp/ps_time/tasks.json", "w"))
for _, f in pick: shutil.copy(f"{src}/{f}", f"/tmp/ps_time/set/{f}")
print("picked", len(pick))
E
export PYTHONUNBUFFERED=1 TORCH_DISABLE_NATIVE_JIT=1 PYTHONPATH=/home/setup/og2/src
PIXI=/home/setup/.pixi/bin/pixi
t0=$(date +%s)
$PIXI run --manifest-path /home/setup/og2/judge-env/pixi.toml python /home/setup/og2/src/desktop/poseswap_score.py /home/setup/og2/judge /tmp/ps_time/tasks.json /home/setup/og2/poseswap /tmp/ps_time/scores.jsonl /tmp/ps_time/set 2>&1 | grep --line-buffered -E "^(SMOKE|SET|SCORE|Traceback|[A-Za-z]*Error)" | awk -v t0=$t0 '{ "date +%s.%N" | getline now; close("date +%s.%N"); printf "%.1f %s\n", now - t0, $0 }'
echo "WALL $(( $(date +%s) - t0 )) s"
