from pydantic import BaseModel, Field
from typing import List, Optional, Any

class Binding(BaseModel):
    role: str
    members: List[str]
    condition: Optional[dict] = None

class Policy(BaseModel):
    bindings: List[Binding]
    etag: Optional[str] = None
    version: int = 1

class Finding(BaseModel):
    id: str = Field(..., description="Unique identifier for the finding type")
    severity: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    description: str
    resource: str = "project-policy"
    details: Any = None
    remediation: Optional[str] = None

class ScenarioCheck(BaseModel):
    name: str
    description: str
    status: str = "PENDING"  # PASS, FAIL, ERROR
    details: Optional[str] = None

class ScenarioResult(BaseModel):
    scenario_name: str
    checks: List[ScenarioCheck]
    actions_required: List[str]
