# ⚡ AegisVolt | Plataforma cloud-native EV

**Entrega académica reproducible para Linux**. Tres microservicios (Station, Billing, Energy), gateway GraphQL, SAGA compensatoria, feature flags por ambiente, DynamoDB local mediante Floci, Terraform, Compose, Kubernetes, CI GitHub Actions y guía de defensa.

## Ejecución rápida

```bash
chmod +x scripts/*.sh
./scripts/launch.sh dev
./scripts/launch.sh test
./scripts/launch.sh prod
./scripts/demo.sh
```

| Ambiente | UI | GraphQL | Floci |
|---|---|---|---|
| dev | http://localhost:8080 | http://localhost:8000/graphql | http://localhost:4566 |
| test | http://localhost:8081 | http://localhost:8001/graphql | http://localhost:4567 |
| prod (simulada) | http://localhost:8082 | http://localhost:8002/graphql | http://localhost:4568 |

La interfaz muestra conectores, saldo, flags, historial de SAGA, compensaciones y telemetría. Cambios de flags se persisten por ambiente y se observan sin redeploy con polling de 5 s.

## Qué contiene

- `app/`: servicios Station, Billing y Energy y API GraphQL.
- `frontend/`: dashboard web sin proceso de build.
- `infra/terraform/`: workspaces y módulos de DynamoDB, CloudWatch y red AWS opcional.
- `infra/terraform-backend/`: manual de S3 remoto versionado.
- `k8s/`: base, overlays dev/test/prod, Floci emulado local y canary ingress-nginx.
- `observability/flows.py`: auditoría Prefect.
- `.github/workflows/`: pipeline CI con gates y deployment self-hosted condicionado.
- `tests/`: pruebas unitarias, de integración y E2E.
- `docs/SUSTENTACION.md`: preguntas del profesor contestadas con evidencias y advertencias.
- `docs/ARQUITECTURA.md`: secuencia SAGA, C4 simplificado, decisiones y limitaciones.
- `docs/INSTALACION_LINUX.md`: guía de instalación y troubleshooting.
- `docs/MATRIZ_CUMPLIMIENTO.md`: contraste real con la rúbrica.

## Advertencia técnica
El proyecto es un **prototipo educativo**, no un servicio listo para producción. La capa de red VPC/VPCE real, integración EKS y APIGW privado, protección de branches, despliegue canary automatizado por métricas, backend S3 activado y servidor Prefect persistente requieren configuración adicional en la infraestructura del alumno. No se atribuye equivalencia absoluta a Floci o al clúster local. Véase la matriz de cumplimiento.

## Seguridad
Nunca exponer esta demo a Internet. No tiene autenticación/RBAC; los valores AWS `test` son datos ficticios solo para Floci. Para AWS real usar roles IAM, TLS y secretos protegidos.


## Corrección 2026-11-09 (gateway reiniciando)

Si obtienes `ImportError: cannot import name ExecutionContext` o `curl: (7)` en el puerto 8001, consulta [CORRECCION_GATEWAY_2026-11-09.md](docs/CORRECCION_GATEWAY_2026-11-09.md). Esta versión fija `graphql-core` y comprueba el arranque del gateway.

## Corrección DynamoDB de SAGA (9 nov 2026)

Ver `docs/CORRECCION_DYNAMODB_2026-11-09.md`.


## Diagnóstico de 8002 y recuperación de SAGA (v3)

Para conocer qué ambiente está accesible: `./scripts/status.sh test` y `./scripts/status.sh prod`.
El HTML de `8082` puede responder aunque la API `8002` esté apagada. Inicia `prod` con `./scripts/launch.sh prod`.
Para inspeccionar y, tras revisión, recuperar una transacción atascada: `./scripts/recover.sh test`.
Consulta `docs/DIAGNOSTICO_AMBIENTES_2026-11-09.md` antes de utilizar `--apply`.
