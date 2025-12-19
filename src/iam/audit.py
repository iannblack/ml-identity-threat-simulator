from __future__ import annotations
import argparse, json, os
from src.iam.parsers import load_json, extract_bindings_from_policy

RISKY_ROLES = {"roles/owner", "roles/editor", "roles/bigquery.admin", "roles/storage.admin"}
WILDCARDS = {"allUsers", "allAuthenticatedUsers"}

def score_binding(binding):
    score = 0
    reason = []
    role = binding["role"]
    member = binding["member"]
    if role in RISKY_ROLES:
        score += 5; reason.append(f"risky-role:{role}")
    if member in WILDCARDS or member.endswith(":allUsers") or member.endswith(":allAuthenticatedUsers"):
        score += 5; reason.append("wildcard-member")
    if member.startswith("serviceAccount:") and role in {"roles/owner","roles/editor"}:
        score += 3; reason.append("sa-high-priv")
    return score, reason

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", required=True, help="CAI assets export (unused in this minimal demo)")
    ap.add_argument("--policy", required=True, help="Project IAM policy JSON")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    policy = load_json(args.policy)
    bindings = extract_bindings_from_policy(policy)
    findings = []
    for b in bindings:
        score, reason = score_binding(b)
        if score > 0:
            findings.append({"binding": b, "score": score, "reason": reason})

    findings_path = os.path.join(args.out, "findings.json")
    with open(findings_path, "w") as f:
        json.dump({"findings": findings, "total": len(findings)}, f, indent=2)
    print(f"Wrote {findings_path} with {len(findings)} risky bindings")
