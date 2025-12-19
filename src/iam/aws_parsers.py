from __future__ import annotations

import json
from typing import Any

from src.core.models import AwsPolicy, AwsStatement


def load_aws_policy_from_json(path: str) -> AwsPolicy:
    """Loads an AWS IAM Policy from a JSON file."""
    with open(path) as f:
        data = json.load(f)

    # AWS JSON policies sometimes have a single Statement which is a dict, not a list
    # We need to normalize this list
    raw_statements = data.get("Statement", [])
    if isinstance(raw_statements, dict):
        raw_statements = [raw_statements]

    statements = []
    for s in raw_statements:
        statements.append(AwsStatement(**s))

    return AwsPolicy(
        Version=data.get("Version", "2012-10-17"),
        Id=data.get("Id"),
        Statement=statements,
    )
