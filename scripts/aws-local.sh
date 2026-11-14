#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-dev}"; shift || true
case "$ENVIRONMENT" in dev) PORT=4566;;test) PORT=4567;;prod) PORT=4568;;*) exit 2;;esac
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
  aws --endpoint-url "http://localhost:$PORT" "$@"
