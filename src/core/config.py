import yaml
import os
from pydantic import BaseModel
from typing import List

class AppConfig(BaseModel):
    risky_roles: List[str]
    wildcard_members: List[str]
    
    @classmethod
    def load(cls, path: str = "config.yaml") -> "AppConfig":
        if not os.path.exists(path):
            # Fallback defaults if config missing
            return cls(
                risky_roles=["roles/owner", "roles/editor"],
                wildcard_members=["allUsers", "allAuthenticatedUsers"]
            )
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            
        return cls(**data)
