#!/usr/bin/env python3
"""Add the SolidCraft CAD guest's five host-callable functions as actions, in a module `cad-guest`.
The functions and their signatures are the lines of V-Sekai-fire/interactor-solidcraft-guest sigs/solidcraft.sigs (tools/solidcraft.sigs, read 2026-11-15), which is the
guest's source of truth for its public surface; its README lists three of the five. Each action needs the guest repository checked out, solidcraft-guest.elf built and the
engine checkout (bherbruck/solidcraft) on hand, and sets that the function ran. No duration is stated: none has been timed here.
usage: tools/add_cad_guest_actions.py   (once; it refuses to run twice), then the tests"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev = lambda p: {"eval": {"type": "pointer/ge", "pointer": p, "value": 1}}; st = lambda p: {"pointer/set": p, "value": 1}
fns = []
for line in open(f"{ROOT}/tools/solidcraft.sigs"):
    m = re.match(r"SolidCraft\.(\w+)\((.*?)\)\s*->\s*(\w+)\s*(?:#\s*(.*))?$", line.strip())
    if m: fns.append(m.groups())
assert len(fns) == 5, fns
actions, methods = {}, {}
for name, args, ret, note in fns:
    a = name.replace("_", "-"); sig = f"SolidCraft.{name}({args}) -> {ret}"
    actions[a] = {"params": [], "body": [ev("/cad_input/solidcraft_engine"), ev("/cad_input/guest_repo"), ev("/cad_input/guest_elf"), st(f"/cad/{name}")],
                  "description": f"{sig}: {note}." if note else f"{sig}.", "description_basis": "written: the line of sigs/solidcraft.sigs of V-Sekai-fire/interactor-solidcraft-guest for this function, read 2026-11-15",
                  "duration_basis": "not timed: no call of this function has been timed here"}
    methods[f"/cad/{name}"] = {"alternatives": [{"name": "call", "subtasks": [[a]]}]}
names = [n for n, *_ in fns]
variables = [{"name": "cad_input", "type": "int", "description": "1 when what the CAD guest needs is on hand: the SolidCraft engine checkout (solidcraft_engine), the guest repository (guest_repo) and solidcraft-guest.elf built (guest_elf).", "init": {}},
             {"name": "cad", "type": "int", "description": "1 when the CAD guest function of that name has run: " + ", ".join(names) + ".", "init": {}}]
mod = {"@context": {"VSEKAI": "https://v-sekai.org/", "domain": "VSEKAI:planning/domain/"}, "@type": "domain:Definition", "name": "cad_guest", "module": "cad-guest", "variables": variables, "actions": actions, "methods": methods}
F = f"{ROOT}/domains/presence-edit.jsonld"; d = json.load(open(F)); assert "solid-box" not in d["actions"], "already added"
d["variables"] += variables; d["actions"].update(actions); d["methods"].update(methods)
dump = lambda o, f: (json.dump(o, open(f, "w"), indent=1, ensure_ascii=False), open(f, "a").write("\n"))
dump(d, F); dump(mod, f"{ROOT}/domains/modules/cad-guest.jsonld")
I = f"{ROOT}/domains/modules/index.json"; ix = json.load(open(I)); ix["variables"] += variables; ix["order"]["actions"] += list(actions); ix["order"]["methods"] += list(methods)
if "cad-guest" not in ix["modules"]: ix["modules"].append("cad-guest")
dump(ix, I)
p = json.load(open(f"{ROOT}/problems/guest-elf-ready.jsonld")); p["name"] = "cad_guest_ready_problem"; p["description"] = "The SolidCraft engine checked out, the CAD guest built: call each of its five functions."
p["variables"] = [{"name": "cad_input", "type": "int", "init": {"solidcraft_engine": 1, "guest_repo": 1, "guest_elf": 1}}, {"name": "cad", "type": "int", "init": {n: 0 for n in names}}]
p["todo_list"] = [{"goal": [{"pointer": f"/cad/{n}", "eq": 1} for n in names]}]
dump(p, f"{ROOT}/problems/cad-guest-ready.jsonld"); print(len(actions), "actions")
