from __future__ import annotations

import json

from src.core.models import Binding, Policy


def load_policy_from_json(path: str) -> Policy:
    """Loads a IAM Policy from a JSON file."""
    with open(path) as f:
        data = json.load(f)

    # Adapt raw JSON to Pydantic model if necessary
    # GCP Policy JSON usually has "bindings", "etag", "version"
    bindings = []
    for b in data.get("bindings", []):
        bindings.append(
            Binding(role=b["role"], members=b.get("members", []), condition=b.get("condition"))
        )

    return Policy(bindings=bindings, etag=data.get("etag"), version=data.get("version", 1))
