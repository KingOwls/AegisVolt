#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-dev}";ACTION="${2:-plan}"
case "$ENVIRONMENT" in dev) PORT=4566;;test) PORT=4567;;prod) PORT=4568;;*) exit 2;;esac
cd "$(dirname "$0")/../infra/terraform"
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1
export TF_VAR_endpoint="http://localhost:$PORT" TF_VAR_local_emulation=true
terraform init -backend=false
terraform workspace select "$ENVIRONMENT" || terraform workspace new "$ENVIRONMENT"
terraform "$ACTION" -var="enable_network=false" ${@:3}
# For S3-backed state use infra/terraform-backend/README.md; local -backend=false is not rubric-compliant.
