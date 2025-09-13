from typing import Any, List
import json
def load_json(path: str) -> Any:
    with open(path) as f: return json.load(f)
def extract_bindings_from_policy(policy: dict) -> List[dict]:
    out=[]; 
    for b in policy.get("bindings", []):
        for m in b.get("members", []):
            out.append({"role": b.get("role"), "member": m})
    return out
