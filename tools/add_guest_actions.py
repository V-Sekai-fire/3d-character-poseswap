#!/usr/bin/env python3
"""Add one action per godot-sandbox guest ELF that serves the pipeline, as a module `guest-elf`, to the single domain file, the index and the problem set.
Each action needs the guest's repository checked out and its ELF built, and sets that the guest has run. A guest whose compute is GPU-only also takes the GPU.
The description is the first sentence of the repository's README (tools/guest_meta.json, read from GitHub on 2026-11-15). No duration is stated: none of these has been timed here.
usage: tools/add_guest_actions.py   (once; it refuses to run twice), then the tests"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); meta = json.load(open(f"{ROOT}/tools/guest_meta.json"))
GUESTS = ["usd", "udim-unpack", "remesh", "cage", "drape", "cloth-fit", "garment-fit", "headfit", "skintokens", "skintokens-rig", "pixal3d", "seethrough"]
GPU = {"cloth-fit", "skintokens", "skintokens-rig", "pixal3d", "seethrough"}      # the README says the compute is on the GPU (cloth-fit: no CPU path; ggml-rd; RenderingDevice)
k_ = lambda g: g.replace("-", "_")
def first_sentence(t):
    t = re.sub(r"\s+", " ", re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t.replace("`", ""))).strip(); m = re.match(r"(.+?[.!?])(?:\s|$)", t); return (m.group(1) if m else t).strip()
ev = lambda p: {"eval": {"type": "pointer/ge", "pointer": p, "value": 1}}; st = lambda p: {"pointer/set": p, "value": 1}
actions, methods = {}, {}
for g in GUESTS:
    k = k_(g); m = meta[g]; body = ([ev("/input/gpu")] if g in GPU else []) + [ev(f"/guest_input/{k}_repo"), ev(f"/guest_input/{k}_elf"), st(f"/guest/{k}")] + ([st("/input/gpu")] if g in GPU else [])
    actions[f"run-{g}-guest"] = {"params": [], "body": body, "description": first_sentence(m["first"]),
        "description_basis": f"written: the first sentence of the README of V-Sekai-fire/{m['repo']}, read 2026-11-15",
        "duration_basis": "not timed: no run of this guest has been timed here"}
    methods[f"/guest/{k}"] = {"alternatives": [{"name": "run", "subtasks": [[f"run-{g}-guest"]]}]}
variables = [{"name": "guest_input", "type": "int", "description": "1 when a guest of the sandbox is ready to run: its repository is checked out (<name>_repo) or its ELF is built (<name>_elf), for " + ", ".join(k_(g) for g in GUESTS) + ".", "init": {}},
             {"name": "guest", "type": "int", "description": "1 when the guest ELF of that name has run its stage: " + ", ".join(k_(g) for g in GUESTS) + ".", "init": {}}]
mod = {"@context": {"VSEKAI": "https://v-sekai.org/", "domain": "VSEKAI:planning/domain/"}, "@type": "domain:Definition", "name": "guest_elf", "module": "guest-elf", "variables": variables, "actions": actions, "methods": methods}
F = f"{ROOT}/domains/presence-edit.jsonld"; d = json.load(open(F))
assert "run-usd-guest" not in d["actions"], "already added"
d["variables"] += variables; d["actions"].update(actions); d["methods"].update(methods)
dump = lambda o, f: (json.dump(o, open(f, "w"), indent=1, ensure_ascii=False), open(f, "a").write("\n"))
dump(d, F); dump(mod, f"{ROOT}/domains/modules/guest-elf.jsonld")
I = f"{ROOT}/domains/modules/index.json"; ix = json.load(open(I)); ix["variables"] = ix.get("variables", []) + variables
ix["order"]["actions"] += list(actions); ix["order"]["methods"] += list(methods)
if "guest-elf" not in ix["modules"]: ix["modules"].append("guest-elf")
dump(ix, I)
# a problem with every guest ready and the GPU free, whose goal is that all of them have run
p = json.load(open(f"{ROOT}/problems/relay-loop-ready.jsonld")); p["name"] = "guest_elf_ready_problem"; p["description"] = "Every guest ELF built and its repository checked out, a free GPU: run them all."
gi = {f"{k_(g)}_{s}": 1 for g in GUESTS for s in ("repo", "elf")}
p["variables"] = [{"name": "input", "type": "int", "description": "1 when an input is on hand: a free GPU.", "init": {"gpu": 1}}, {"name": "guest_input", "type": "int", "description": variables[0]["description"], "init": gi},
                  {"name": "guest", "type": "int", "description": variables[1]["description"], "init": {k_(g): 0 for g in GUESTS}}]
p["todo_list"] = [{"goal": [{"pointer": f"/guest/{k_(g)}", "eq": 1} for g in GUESTS]}]
dump(p, f"{ROOT}/problems/guest-elf-ready.jsonld"); print(len(actions), "actions,", len(methods), "methods")
