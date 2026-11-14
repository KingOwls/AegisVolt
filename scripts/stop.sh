#!/usr/bin/env bash
set -euo pipefail
case "${1:-dev}" in
 dev) export AWS_PORT=4566 API_PORT=8000 WEB_PORT=8080;;
 test) export AWS_PORT=4567 API_PORT=8001 WEB_PORT=8081;;
 prod) export AWS_PORT=4568 API_PORT=8002 WEB_PORT=8082;;
 *) exit 2;;
esac
export APP_ENV="${1:-dev}"
docker compose -p "aegisvolt-$APP_ENV" down
