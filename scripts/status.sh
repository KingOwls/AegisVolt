#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-test}"
case "$ENVIRONMENT" in
  dev) API_PORT=8000; WEB_PORT=8080; AWS_PORT=4566;;
  test) API_PORT=8001; WEB_PORT=8081; AWS_PORT=4567;;
  prod) API_PORT=8002; WEB_PORT=8082; AWS_PORT=4568;;
  *) echo 'Uso: ./scripts/status.sh dev|test|prod' >&2; exit 2;;
esac
printf '== Estado Docker: %s ==\n' "$ENVIRONMENT"
docker compose -p "aegisvolt-$ENVIRONMENT" ps -a
printf '\n== Puertos del ambiente ==\n'
for endpoint in "gateway|http://127.0.0.1:$API_PORT/health" "frontend|http://127.0.0.1:$WEB_PORT/" "floci|http://127.0.0.1:$AWS_PORT/_localstack/health"; do
  service="${endpoint%%|*}"; url="${endpoint#*|}"
  if [ "$service" = 'floci' ]; then
    url="http://127.0.0.1:$AWS_PORT/"
  fi
  code=$(curl -sS --max-time 3 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)
  printf '%-9s %-52s HTTP %s\n' "$service" "$url" "${code:-sin conexión}"
done
printf '\nEl frontend puede abrir aunque el gateway esté detenido.\n'
printf 'Si el gateway no responde, revisa: docker compose -p aegisvolt-%s logs --tail=100 gateway\n' "$ENVIRONMENT"
