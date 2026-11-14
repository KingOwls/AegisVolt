#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-dev}"
case "$ENVIRONMENT" in
  dev) export AWS_PORT=4566 API_PORT=8000 WEB_PORT=8080;;
  test) export AWS_PORT=4567 API_PORT=8001 WEB_PORT=8081;;
  prod) export AWS_PORT=4568 API_PORT=8002 WEB_PORT=8082;;
  *) echo 'Uso: ./scripts/launch.sh dev|test|prod'; exit 2;;
esac
export APP_ENV="$ENVIRONMENT"
docker compose -p "aegisvolt-$APP_ENV" up -d --build
echo 'Verificando disponibilidad del gateway GraphQL...'
READY=0
for attempt in $(seq 1 45); do
  if curl --silent --fail --max-time 2 "http://127.0.0.1:${API_PORT}/health" > /dev/null; then
    READY=1
    break
  fi
  if [ "$(docker compose -p "aegisvolt-$APP_ENV" ps --status restarting --services | grep -cx gateway || true)" -gt 0 ]; then
    echo 'Gateway en reinicio: consultando registros de errores.' >&2
    docker compose -p "aegisvolt-$APP_ENV" logs --tail 45 gateway >&2
    exit 1
  fi
  sleep 2
done
if [ "$READY" -ne 1 ]; then
  echo "Error: el gateway no respondió en http://127.0.0.1:${API_PORT}/health" >&2
  docker compose -p "aegisvolt-$APP_ENV" logs --tail 65 gateway >&2
  exit 1
fi
printf 'AegisVolt %s: http://localhost:%s | GraphQL: http://localhost:%s/graphql | Floci: http://localhost:%s\n' "$APP_ENV" "$WEB_PORT" "$API_PORT" "$AWS_PORT"
