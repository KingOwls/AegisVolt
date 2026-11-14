# Instalación Linux, desde cero

Requisitos: Linux x86_64/arm64, Docker Engine 24+ con plugin Compose v2, Git, curl. Para IaC: Terraform 1.7+, AWS CLI v2. Para Kubernetes: kubectl + k3d/kind + ingress-nginx, y Floci accesible desde pods. 8 GB RAM recomendados.

1. Comprobar Docker: `docker version && docker compose version`.
2. Descomprimir ZIP y entrar a `AegisVolt`.
3. Ejecutar `chmod +x scripts/*.sh`.
4. Iniciar desarrollo: `./scripts/launch.sh dev`.
5. Abrir UI `http://localhost:8080`, GraphQL `http://localhost:8000/graphql` y API Floci `http://localhost:4566`. El bootstrap crea seis tablas DynamoDB, tres bahías y una billetera de prueba.
6. Iniciar test: `./scripts/launch.sh test` (UI 8081, GraphQL 8001, Floci 4567).
7. Iniciar prod **simulada**: `./scripts/launch.sh prod` (UI 8082, GraphQL 8002, Floci 4568).
8. Provocar avería de prueba: `./scripts/demo.sh` (usa test).
9. Revisar logs: `docker compose -p aegisvolt-test logs -f gateway`.
10. Inspeccionar tablas: `./scripts/aws-local.sh test dynamodb list-tables` y `./scripts/aws-local.sh test dynamodb scan --table-name aegisvolt-test-sagas`.
11. Tests: crear venv `python3 -m venv .venv; source .venv/bin/activate; pip install -r requirements-dev.txt; pytest -q tests/test_unit.py`. Integración/E2E necesitan Compose test activo: `AEGIS_INTEGRATION=1 AEGIS_API=http://localhost:8001/graphql pytest tests/test_integration.py`, `AEGIS_E2E=1 AEGIS_API=http://localhost:8001/graphql pytest tests/test_e2e.py`.
12. Detener cada ambiente: `./scripts/stop.sh dev`, idem test/prod. **No ejecutar `down -v` si desea conservar la persistencia**.

## Terraform
Ver `infra/terraform-backend/README.md`. Quickstart no crea backend remoto automáticamente y no debe confundirse con requisito S3. `./scripts/terraform-local.sh dev plan` utiliza state local, solo para practicar plan. Use `terraform init -backend-config=...` y workspaces cuando presente evidencia S3 versionado.

## Kubernetes
`./scripts/k8s-local.sh dev` aplica los deployments. Requiere preparar k3d/kind y preferiblemente ingress-nginx. El script levanta Floci dentro del namespace y ejecuta un Job para crear DynamoDB. **Atención:** el almacenamiento `emptyDir` se pierde al recrear el pod Floci; use PVC para conservar datos. No se lanza EKS real. Para acceso sin ingress: `kubectl -n aegisvolt-dev port-forward svc/gateway 8000:8000`.

## Diagnóstico
- `Connection refused` a Floci: `docker compose -p aegisvolt-dev ps` y `logs floci`.
- UI responde pero GraphQL no: confirmar puerto API y observar errores CORS/red.
- DynamoDB falta tabla: volver a ejecutar bootstrap `docker compose -p aegisvolt-test run --rm init`.
- Fallan probes Kubernetes: revisar Floci e inicialización `kubectl -n aegisvolt-dev logs deploy/gateway`.
- Prefect: `source .venv/bin/activate; export APP_ENV=test AWS_ENDPOINT_URL=http://localhost:4567 GATEWAY_HEALTH_URL=http://localhost:8001; python -m observability.flows`.
