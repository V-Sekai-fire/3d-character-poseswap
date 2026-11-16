#!/usr/bin/env python3
"""Give every action of domains/presence-edit.jsonld a `description`, and say where it came from in `description_basis`.
written  : the sentence the domain's own description already gives for that action ("relabel-coco: Map every source class ...;"), copied word for word.
drafted  : built from the action's own preconditions and effects, "Needs A, B. Makes C.", with no other source; to be edited by a person who knows the action.
The text built from reads and sets uses only names the action already states. A fact the action both reads and sets (the GPU it takes and gives back) is left out.
usage: tools/set_action_descriptions.py   then tools/sync_modules.py and the three tests"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = f"{ROOT}/domains/presence-edit.jsonld"
d = json.load(open(F)); acts = d["actions"]; text = d["description"]
WORDS = {"gpu_host": "a free GPU host", "edit_prompt": "an edit prompt"}
def say(pointer, setting):
    _, grp, key = pointer.split("/"); k = key.replace("_", " ")
    if key in WORDS and not setting: return WORDS[key]
    return {"part": f"the {k} repository checked out", "input": f"the {k} on hand", "model": f"the {k} loaded", "image": f"the {k} image", "body": f"the body {k}",
            "avatar": f"the avatar {k}", "op": f"the {k} op checked", "aux": k, "course": k, "course_input": f"the {k} on hand", "relay": k,
            "relay_input": f"the {k} on hand", "switch": f"the {k} stage on", "bypass": f"the {k} stage bypassed"}.get(grp, k)
def join(xs): return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
written = drafted = 0
for k, a in acts.items():
    m = re.search(r"(?:^|[\s;])" + re.escape(k) + r": (.+?)(?:\.(?:; | [A-Z]|$)|; |$)", text)
    if m: a["description"], a["description_basis"] = m.group(1).strip() + ".", "written: the sentence the domain description gives for this action"; written += 1; continue
    reads = [b["eval"]["pointer"] for b in a["body"] if "eval" in b]; sets = [b["pointer/set"] for b in a["body"] if "pointer/set" in b]
    both = set(reads) & set(sets); reads = [r for r in reads if r not in both]; sets = [s for s in sets if s not in both]
    parts = ([f"Needs {join([say(r, False) for r in reads])}."] if reads else []) + ([f"Makes {join([say(s, True) for s in sets])}."] if sets else [])
    a["description"] = " ".join(parts) or "A bookkeeping step: it states no fact it needs and sets none."
    a["description_basis"] = "drafted from the action's own preconditions and effects; no other source"; drafted += 1
json.dump(d, open(F, "w"), indent=1, ensure_ascii=False); open(F, "a").write("\n"); print(f"{written} written, {drafted} drafted")
