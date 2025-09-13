#!/usr/bin/env bash
set -euo pipefail
echo "[demo] Simulating SA compromise and revocation steps..."
echo "1) Disable SA key (if present)"
echo "2) Remove high-privilege role"
echo "3) Rotate secrets and trigger re-deploy"
