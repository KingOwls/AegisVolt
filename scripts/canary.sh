#!/usr/bin/env bash
set -euo pipefail
NS="aegisvolt-${1:-dev}"; ACTION="${2:-start}"
case "$ACTION" in
 start)
  kubectl -n "$NS" apply -f k8s/canary/gateway-canary.yaml
  kubectl -n "$NS" rollout status deployment/gateway-canary --timeout=120s
  kubectl -n "$NS" get ingress aegisvolt-api-canary -o yaml
  echo '20% configured via ingress-nginx. Run canary verification BEFORE promote.';;
 promote)
  kubectl -n "$NS" set image deployment/gateway gateway=aegisvolt:canary
  kubectl -n "$NS" rollout status deployment/gateway --timeout=120s
  kubectl -n "$NS" delete -f k8s/canary/gateway-canary.yaml --ignore-not-found
  echo 'Stable promoted to canary image.';;
 rollback)
  kubectl -n "$NS" delete -f k8s/canary/gateway-canary.yaml --ignore-not-found
  echo 'Canary route removed; stable unaffected.';;
 *) echo 'start|promote|rollback';exit 2;;
esac
