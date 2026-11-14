#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-test}"
case "$ENVIRONMENT" in dev|test|prod) ;; *) echo 'Uso: ./scripts/recover.sh test [--saga-id UUID] [--apply]' >&2; exit 2;; esac
shift || true
# The image must have been rebuilt since scripts/recover_sagas.py was added.
if ! docker compose -p "aegisvolt-$ENVIRONMENT" exec -T gateway python -c 'import scripts.recover_sagas' >/dev/null 2>&1; then
  echo 'No se encuentra scripts.recover_sagas dentro de gateway.' >&2
  echo "Actualiza la carpeta del proyecto y ejecuta primero: ./scripts/launch.sh $ENVIRONMENT" >&2
  exit 1
fi
docker compose -p "aegisvolt-$ENVIRONMENT" exec -T gateway python -m scripts.recover_sagas "$@"
