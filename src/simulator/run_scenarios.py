from __future__ import annotations
import argparse, yaml, json, os

def run_scenario(path):
    with open(path, "r") as f:
        sc = yaml.safe_load(f)
    return {"name": sc.get("name"), "checks": sc.get("checks", []), "actions": sc.get("actions", [])}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", default="artifacts/scenario.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    res = run_scenario(args.scenario)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"Wrote {args.out}")
