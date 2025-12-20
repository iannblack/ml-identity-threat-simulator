from __future__ import annotations

import json
import logging

from src.core.models import AzureRoleDefinition

logger = logging.getLogger("iam-simulator")


def load_azure_role_from_json(path: str) -> AzureRoleDefinition:
    """Loads an Azure Role Definition from a JSON file."""
    with open(path) as f:
        data = json.load(f)

    # Handle list input (e.g. from 'az role definition list')
    if isinstance(data, list):
        if len(data) == 0:
            msg = "JSON file contains an empty list of roles"
            raise ValueError(msg)
        if len(data) > 1:
            logger.warning("JSON file contains multiple roles. Auditing the first one only.")
        data = data[0]

    # Handle 'properties' wrapper (common in ARM templates)
    if "properties" in data:
        props = data["properties"]
        # Merge properties into top level definitions for simpler Pydantic parsing
        # or just pass data if flat.
        # Let's simple create a dict that combines what we need.
        merged_data = {
            "name": data.get("name"),
            "roleName": props.get("roleName"),
            "description": props.get("description"),
            "actions": props.get("permissions", [{}])[0].get("actions", []),
            "notActions": props.get("permissions", [{}])[0].get("notActions", []),
            "assignableScopes": props.get("assignableScopes", []),
            "isCustom": (props.get("type", "") == "CustomRole"),
        }
        return AzureRoleDefinition(**merged_data)

    return AzureRoleDefinition(**data)
