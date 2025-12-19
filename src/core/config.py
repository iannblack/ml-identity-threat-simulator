import os

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    risky_roles: list[str]
    wildcard_members: list[str]

    @classmethod
    def load(cls, path: str = "config.yaml") -> "AppConfig":
        if not os.path.exists(path):
            # Fallback defaults if config missing
            return cls(
                risky_roles=["roles/owner", "roles/editor"],
                wildcard_members=["allUsers", "allAuthenticatedUsers"],
            )

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)
