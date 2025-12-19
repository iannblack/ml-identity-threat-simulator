from typing import Any

from pydantic import BaseModel, Field


class Binding(BaseModel):
    role: str
    members: list[str]
    condition: dict | None = None


class Policy(BaseModel):
    bindings: list[Binding]
    etag: str | None = None
    version: int = 1


class Finding(BaseModel):
    id: str = Field(..., description="Unique identifier for the finding type")
    severity: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    description: str
    resource: str = "project-policy"
    details: Any = None
    remediation: str | None = None


class ScenarioCheck(BaseModel):
    name: str
    description: str
    status: str = "PENDING"  # PASS, FAIL, ERROR
    details: str | None = None


class ScenarioResult(BaseModel):
    scenario_name: str
    checks: list[ScenarioCheck]
    actions_required: list[str]
