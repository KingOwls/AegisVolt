#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8001/graphql}"
BASE="${API%/graphql}"
if ! curl -fsS --max-time 5 "$BASE/health" > /dev/null; then
  echo "ERROR: gateway no disponible en $BASE. Comprueba docker compose -p aegisvolt-test logs --tail 100 gateway" >&2
  exit 1
fi
request() {
  local query="$1" response
  response=$(curl --fail --show-error --silent --max-time 25 "$API" -H 'Content-Type: application/json' -d "$(python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1]}))' "$query")")
  printf '%s' "$response" | python3 -c 'import json,sys; v=json.load(sys.stdin); print(json.dumps(v,indent=2,ensure_ascii=False)); sys.exit(1 if v.get("errors") else 0)'
}
cleanup() {
  if [ "${FLAG_ENABLED:-0}" = 1 ]; then
    echo 'Restaurando flag de fallo a false...'
    request 'mutation {setFlag(key:"SIMULATE_CHARGER_HARDWARE_FAULT",enabled:false){key enabled}}' || true
  fi
}
trap cleanup EXIT
printf '%s\n' '[1] Activar fallo de hardware en test'
request 'mutation {setFlag(key:"SIMULATE_CHARGER_HARDWARE_FAULT",enabled:true){key enabled}}'
FLAG_ENABLED=1
printf '%s\n' '[2] Lanzar SAGA que deberá compensarse'
# Selecciona conector disponible para que la demo funcione aunque BAY-01 esté ocupado.
CONNECTOR=$(curl -fsS "$API" -H 'Content-Type: application/json' -d '{"query":"{connectors{id status}}"}' | python3 -c 'import json,sys; p=json.load(sys.stdin); assert not p.get("errors"),p; print(next((r["id"] for r in p["data"]["connectors"] if r["status"]=="AVAILABLE"),""))')
if [ -z "$CONNECTOR" ]; then
  echo 'No hay conectores AVAILABLE; revisa reservas y compensaciones anteriores.' >&2
  exit 1
fi
request "mutation {reserveAndActivate(connectorId:\"$CONNECTOR\",fleetId:\"FLEET-DEMO\"){id status events error}}"
printf '%s\n' '[3] Consultar saldo, conector e historial'
request '{connectors{id status} wallets{fleetId balance} transactions{id status events error}}'
