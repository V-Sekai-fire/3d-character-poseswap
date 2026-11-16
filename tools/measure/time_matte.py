"""Time the matte-image step: BiRefNet-matting soft alpha of one portrait, the way HairDeck's preprocessing runs it (size 1024, half precision).
Reports the one-time model load and then N inference runs, in seconds, with the GPU synchronised around each. Like `score`, the one-time load is kept out of
the per-image duration, because no action models it.
usage: HAIRDECK_ROOT=<ws> RUNS=6 pixi run --manifest-path ~/og2/hairdeck/pixi.toml python tools/measure/time_matte.py <portrait> > tests/evidence/matte_times.json
The HairDeck checkout (hairdeck/ package) must be importable: run it from the HairDeck folder with PYTHONPATH pointing at it."""
import json, os, sys, time, statistics
import numpy as np
from PIL import Image
import torch
from hairdeck.prep import matte

N = int(os.environ.get("RUNS", "6"))
img = np.asarray(Image.open(sys.argv[1]).convert("RGB"))

def sync(): torch.cuda.synchronize()
sync(); t = time.perf_counter(); net = matte.build("birefnet_matting", 1024, device="cuda"); sync(); load = time.perf_counter() - t
runs = []; last = None
for _ in range(N):
    sync(); t = time.perf_counter(); a = net(img); sync(); runs.append(time.perf_counter() - t); last = a
a = last.cpu().numpy()
print(json.dumps({"matte-image": {"runs_s": [round(r, 4) for r in runs], "model_load_s": round(load, 3), "input": [int(img.shape[1]), int(img.shape[0])],
                                  "alpha_min": float(a.min()), "alpha_max": float(a.max()), "alpha_mean": round(float(a.mean()), 4),
                                  "device": torch.cuda.get_device_name(0), "torch": torch.__version__}}, indent=1))
