#!/usr/bin/env bash
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
# Export CAI (resources) and IAM policy
GCS=gs://$PROJECT_ID-cai-export
(gsutil mb -p $PROJECT_ID -l US $GCS || true)
gcloud asset export --project=$PROJECT_ID --content-type=resource --output-path=$GCS/assets.json
gcloud projects get-iam-policy $PROJECT_ID --format=json > cai/example/policy.json
