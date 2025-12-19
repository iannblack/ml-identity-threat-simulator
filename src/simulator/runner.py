import yaml
from typing import List, Dict
from src.core.models import ScenarioResult, ScenarioCheck

class ScenarioRunner:
    def load_scenario(self, path: str) -> Dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def run(self, scenario_path: str) -> ScenarioResult:
        data = self.load_scenario(scenario_path)
        
        checks = []
        for check_desc in data.get("checks", []):
            # In a real implementation, this would actually execute logic against GCP
            # For simulation purposes, we treat them as descriptions
            checks.append(ScenarioCheck(
                name="Check Rule",
                description=check_desc,
                status="PENDING" 
            ))
            
        return ScenarioResult(
            scenario_name=data.get("name", "Unknown Scenario"),
            checks=checks,
            actions_required=data.get("actions", [])
        )
