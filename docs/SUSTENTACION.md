# Guía de sustentación: banco de respuestas AegisVolt

## 1. ¿Cómo evita que test sobrescriba prod?
`terraform.workspace` crea prefijos `aegisvolt-test-*` y `aegisvolt-prod-*`; el backend S3 usa keys diferenciadas por workspace, normalmente `env:/test/aegisvolt/terraform.tfstate` y `env:/prod/...`. La separación real requiere `terraform init` con S3 remoto: el script rápido `terraform-local.sh` usa estado local y **no** satisface esa comprobación. Presentar `terraform workspace list`, `terraform state list`, DynamoDB `list-tables` y el contenido del bucket.

## 2. ¿Cómo listar y restaurar una versión de tfstate?
`aws s3api list-object-versions --bucket aegisvolt-tfstate-local --prefix 'env:/dev/aegisvolt/terraform.tfstate'`. Descargar la versión específica con `get-object --version-id ...` y guardarla como respaldo, inspeccionarla y restaurarla mediante un procedimiento controlado, por ejemplo `put-object` del archivo validado sobre la key del workspace, conservando versionamiento. Cuidado: el workspace default tiene una ruta distinta. Antes de restaurar, bloquear ejecuciones concurrentes y verificar el `serial`/`lineage`.

## 3. ¿Qué camino recorre un paquete APIGW → Kubernetes?
En AWS real: cliente → API Gateway privado → VPC Interface Endpoint `execute-api` (ENI privada + security group) → integración privada VPC Link → balanceador interno NLB/ALB → Service → pod. Las subredes privadas y la política de endpoints controlan acceso. **El módulo de red incluido crea VPC/subredes/VPCE pero no aprovisiona API Gateway privado, VPC Link, balanceador ni EKS reales**. En Compose: navegador → localhost:8000 → gateway → nombres DNS privados de contenedores. No presentar esta ruta local como VPCE real.

## 4. ¿Cómo bloquear force push / push directo?
En GitHub configurar rulesets/branch protection en `dev`, `test`, `prod`: require pull request, require status checks (lint-build, unit-tests, integration-tests, e2e-tests, terraform-plan), disallow force pushes; no bypass para colaboradores. El ZIP no puede activar estas reglas en el repositorio del alumno. Demostrar rechazo en una rama protegida del repositorio real, sin ejecutar `--force` sobre trabajo importante.

## 5. ¿Cómo el pipeline reconoce el ambiente?
En `.github/workflows/deploy.yml`, `GITHUB_REF_NAME` determina `TARGET_ENV` después del push a `dev`, `test` o `prod`, y ejecuta `terraform workspace select "$TARGET_ENV"`, seguido de `terraform apply`. El runner self-hosted debe tener backend S3 configurado y kubectl. En PR, `github.base_ref` identifica el destino. Flujo recomendado: `feature/* → dev → test → prod` siempre vía PR.

## 6. ¿Qué valida el canary 20% → 100%?
El manifiesto `k8s/canary/gateway-canary.yaml` anota `nginx.ingress.kubernetes.io/canary-weight: "20"` y el script `scripts/canary.sh` permite arrancar, promover o revertir. Para producción hace falta automatizar el criterio: probes de readiness + 5xx por debajo de 1% y latencia p95 bajo umbral durante una ventana, comparando estable/canary. **El script solo valida readiness y NO incluye un gate automático por métricas**. No afirmar que esto ya aprueba promoción automática. Requiere controlador ingress-nginx y métricas de tráfico reales.

## 7. ¿Cómo demostrar compensación SAGA?
Arrancar test `./scripts/launch.sh test`; ejecutar `./scripts/demo.sh`. La flag `SIMULATE_CHARGER_HARDWARE_FAULT` se activa solo en `test`. Saga reserva, cobra, intenta activar, falla, reembolsa y libera. El historial `events` muestra `STARTED → RESERVED → CHARGED → COMPENSATING → REFUNDED → RELEASED`. Consultar `aegisvolt-test-payments`, `-reservations`, `-sagas` en DynamoDB. Verificar que el saldo retorna al valor anterior.

## 8. ¿Cómo garantiza idempotencia?
Reservas usan actualización condicional sobre estado `AVAILABLE`; pagos usan `TransactWriteItems` con un `pk=saga_id` único y condición de no existencia; reembolsos hacen **transacción atómica** entre estado de pago `CHARGED → REFUNDED` y crédito a billetera condicionado al estado anterior; liberación verifica identidad de la saga y estado y responde idempotentemente a reintentos conocidos. Limitación: el orquestador asume que la llamada que responde con error no pudo dejar una transacción confirmada; en una pérdida de respuesta después del commit pueden quedar pasos incompletos. Para producción agregar outbox, cola duradera y reconciliación/reintentos.

## 9. ¿Cómo rastrear Prefect y CloudWatch?
`APP_ENV=test AWS_ENDPOINT_URL=http://localhost:4567 GATEWAY_HEALTH_URL=http://localhost:8001 python -m observability.flows` ejecuta las tasks de salud y auditoría. El código `log` envía eventos JSON a `/aegisvolt/test/gateway` con `correlation_id=saga_id`; con AWS CLI: `./scripts/aws-local.sh test logs describe-log-groups --log-group-name-prefix /aegisvolt/test/`. Para la UI de Prefect iniciar `prefect server start`, configurar `PREFECT_API_URL` y registrar/servir flow. La invocación directa **no publica por sí misma un deployment recurrente**.

## 10. ¿Cómo cambiar flag sin redeploy y aislar prod?
Abrir test y dev en puertos 8081/8080, activar la flag desde la UI de test y observar transacción compensada. La flag persiste en la tabla `aegisvolt-test-flags`, distinta de `aegisvolt-prod-flags`. La UI consulta GraphQL cada 5 segundos. Modificar dev no toca prod, porque las instancias Compose y tablas tienen prefijos separados.

## 11. ¿Por qué SAGA y no una transacción ACID única?
Cada servicio controla tablas propias y representa una frontera de negocio. SAGA coordina pasos locales y compensaciones de negocio en orden inverso, logrando consistencia eventual. La compensación no es rollback de base de datos tradicional.

## 12. ¿Por qué DynamoDB database-per-service?
Cada microservicio administra datos y reglas particulares. En este ejemplo reservas, wallet/pagos, despacho y control/flags/sagas se guardan en tablas separadas; se evita compartir escrituras entre servicios. Las consultas de agregación se hacen desde GraphQL y los invariantes de dinero se resuelven dentro de Billing.

## 13. ¿Qué es GraphQL y por qué se usa?
El cliente pide solo campos necesarios en un endpoint `/graphql`. `Query` devuelve conectores, billeteras, flags, transacciones y telemetría; `Mutation` cambia flags o inicia la saga. El gateway no reemplaza las bases de datos individuales.

## 14. ¿Qué falta para equivalencia completa AWS/EKS?
Un deployment de producción real debe agregar API Gateway privado con resource policy, VPC Link/NLB/ALB, clúster EKS y nodegroups, autenticación IAM/OIDC, TLS/WSS, secretos, políticas de red, HPA, telemetry en tiempo real por streaming, límites de tasa y AWS account real. Floci permite simular APIs pero no demuestra por sí mismo aislamiento de red del kernel AWS. Incluya capturas de evidencias reales en la defensa.
