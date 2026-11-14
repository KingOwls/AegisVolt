# Matriz de cumplimiento honesta frente a la rúbrica

| Requisito | Estado del ZIP | Evidencia o dependencia |
|---|---|---|
| UI panel conectores, flags, saga e historial | Implementado | `frontend/index.html` |
| Tres microservicios Docker | Implementado | `app/*.py`, `compose.yaml` |
| Gateway GraphQL queries/mutations | Implementado | `app/gateway.py` |
| Reserva, cobro, activación SAGA | Implementado | `app/gateway.py` |
| Compensaciones y rollback | Implementado | `tests/test_unit.py`, `scripts/demo.sh` |
| Idempotencia transaccional para cobro/reembolso | Implementado con limitaciones | `app/billing.py`, `docs/ARQUITECTURA.md` |
| Flags aisladas por ambiente sin redeploy | Implementado | Tabla `aegisvolt-{env}-flags` |
| DynamoDB por servicio/ambiente | Implementado | `infra/terraform/modules/persistence`, `bootstrap.py` |
| Terraform workspaces dev/test/prod | Configurado | `infra/terraform/main.tf`, scripts |
| tfstate S3 remoto versionado | Procedimiento, no inicializado | `infra/terraform-backend/README.md` |
| VPC pública/privada, endpoints | Declarado opcional para AWS | `infra/terraform/modules/network`, sin verificación de apply AWS |
| API Gateway privado, VPC Link, EKS | No implementado real | Requiere AWS o prueba de emulación adicional |
| Kubernetes deployments en 3 namespaces | Declarado; requiere clúster | `k8s/base`, `k8s/overlays` |
| CloudWatch JSON con correlation_id | Implementado best effort | `app/common.py`; depende de API Floci |
| Prefect flow audit y health | Implementado invocable | `observability/flows.py`; falta servir/scheduling |
| CI lint/build, unit, integration, E2E | Workflow declarado | `.github/workflows/ci.yml`, falta primera ejecución real |
| CI Terraform plan premerge | Declarado | `terraform-plan` necesita provider y Floci en runner |
| Deploy postmerge por rama | Workflow declarado | `.github/workflows/deploy.yml`, self-hosted y backend configurado |
| Branch protection dev/test/prod | Instrucciones, no aplicado | Hacer rulesets en GitHub |
| Canary 20% ingress-nginx | Manifiesto + script | `k8s/canary`, falta evaluación automatizada de error rate |
| Canary rollback automático por métricas | Pendiente | Definir metric gate con Prometheus/CloudWatch |
| Telemetría tiempo real WSS | Parcial (polling 5 s) | No hay WebSockets ni hardware real |

**Regla:** declarar como completado solo lo ejecutado y demostrado en la máquina o repo del estudiante. No hay evidencias simuladas de CloudWatch, AWS ni GitHub protection.
