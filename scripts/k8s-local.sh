#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-dev}"
case "$ENVIRONMENT" in dev|test|prod);;*) echo 'dev|test|prod';exit 2;;esac
# Requires existing k3d/kind cluster and ingress-nginx. Floci endpoint should be deployed/proxied inside namespace.
docker build -t aegisvolt:local .
if command -v k3d >/dev/null; then k3d image import aegisvolt:local -c "${K3D_CLUSTER:-aegisvolt}"; fi
kubectl apply -k "k8s/overlays/$ENVIRONMENT"
NS="aegisvolt-$ENVIRONMENT"
kubectl -n "$NS" apply -f k8s/floci-local.yaml
kubectl -n "$NS" rollout status deployment/floci --timeout=120s
kubectl -n "$NS" delete job aegisvolt-bootstrap --ignore-not-found
kubectl -n "$NS" apply -f k8s/bootstrap-job.yaml
kubectl -n "$NS" wait --for=condition=complete job/aegisvolt-bootstrap --timeout=180s
kubectl -n "$NS" rollout status deploy/gateway --timeout=120s
printf 'Cluster ready. kubectl -n %s port-forward svc/gateway 8000:8000\n' "$NS"
