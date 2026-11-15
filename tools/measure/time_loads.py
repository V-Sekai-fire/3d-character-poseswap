"""Time each model-loading step of the OmniGen2 edit path, one component at a time, the way omnigen2_edit.py loads them (BF16 base weights + LoRA).
Reports the cold first run and the median of the warm runs, in seconds. Run from ~/og2/src/desktop with `pixi run python time_loads.py`.
  load-qwen25vl-conditioner = mllm + processor, to the GPU        load-omnigen2-transformer = transformer, to the GPU
  load-omnigen2-vae         = vae, to the GPU                      load-editscore-lora       = read the LoRA safetensors file
  merge-editscore-lora      = pipe.load_lora_weights on the assembled pipeline"""
import os, sys, time, json, statistics, gc
from pathlib import Path
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.expanduser("~/og2/src"))
import torch
from diffusers import AutoencoderKL
from transformers import Qwen2_5_VLForConditionalGeneration, Qwen2_5_VLProcessor
from omnigen2.models.transformers.transformer_omnigen2 import OmniGen2Transformer2DModel
from omnigen2.pipelines.omnigen2.pipeline_omnigen2 import OmniGen2Pipeline
from omnigen2.schedulers.scheduling_flow_match_euler_discrete import FlowMatchEulerDiscreteScheduler
from safetensors.torch import load_file
W = Path(os.environ.get("OMNIGEN2_WEIGHTS", os.path.expanduser("~/og2/w"))); base = W / "base"; lora = W / "lora" / "pytorch_lora_weights.safetensors"
dev = torch.device("cuda"); dt = torch.bfloat16; N = int(os.environ.get("RUNS", "4"))
def sync(): torch.cuda.synchronize()
def timed(f):
    sync(); t = time.perf_counter(); r = f(); sync(); return time.perf_counter() - t, r
res = {k: [] for k in ("load-qwen25vl-conditioner", "load-omnigen2-transformer", "load-omnigen2-vae", "load-editscore-lora", "merge-editscore-lora")}
for i in range(N):
    t, mllm = timed(lambda: Qwen2_5_VLForConditionalGeneration.from_pretrained(str(base), subfolder="mllm", torch_dtype=dt).to(dev))
    t2, proc = timed(lambda: Qwen2_5_VLProcessor.from_pretrained(str(base), subfolder="processor")); res["load-qwen25vl-conditioner"].append(t + t2)
    t, tr = timed(lambda: OmniGen2Transformer2DModel.from_pretrained(str(base), subfolder="transformer", torch_dtype=dt).to(dev)); res["load-omnigen2-transformer"].append(t)
    t, vae = timed(lambda: AutoencoderKL.from_pretrained(str(base), subfolder="vae", torch_dtype=dt).to(dev)); res["load-omnigen2-vae"].append(t)
    t, sd = timed(lambda: load_file(str(lora))); res["load-editscore-lora"].append(t)
    sch = FlowMatchEulerDiscreteScheduler.from_pretrained(str(base), subfolder="scheduler")
    pipe = OmniGen2Pipeline(transformer=tr, vae=vae, scheduler=sch, mllm=mllm, processor=proc)
    t, _ = timed(lambda: pipe.load_lora_weights(str(lora.parent), weight_name=lora.name)); res["merge-editscore-lora"].append(t)
    print(f"run {i}: " + " ".join(f"{k.split('-',1)[1]}={v[-1]:.2f}" for k, v in res.items()), flush=True)
    del mllm, tr, vae, pipe, proc, sd; gc.collect(); torch.cuda.empty_cache()
out = {k: {"runs": [round(x, 3) for x in v], "cold": round(v[0], 3), "warm_median": round(statistics.median(v[1:]), 3)} for k, v in res.items()}
print("RESULT " + json.dumps(out)); json.dump(out, open(os.path.expanduser("~/og2/load_times.json"), "w"), indent=1)
