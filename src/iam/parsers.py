from __future__ import annotations
from typing import Any, List
import json

def load_json(path: str) -> Any:
    with open(path, "r") as f:
        return json.load(f)

def extract_bindings_from_policy(policy: dict) -> List[dict]:
    out = []
    for b in policy.get("bindings", []):
        role = b.get("role")
        for m in b.get("members", []):
            out.append({"role": role, "member": m})
    return out
