# ml-identity-threat-simulator
IAM Threat Simulator for ML pipelines on GCP: CAI inventory analysis, risky bindings detection, attack scenarios, and remediation playbooks.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r src/iam/requirements.txt
python src/iam/audit.py --assets cai/example/assets.json --policy cai/example/policy.json --out artifacts
python reports/risk_report.py --findings artifacts/findings.json --out artifacts/report.md
```
