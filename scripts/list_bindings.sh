#!/usr/bin/env bash
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[]" --format="table(bindings.role, bindings.members)"
