# Corrección de inicio del GraphQL Gateway (9 de noviembre de 2026)

## Diagnóstico a partir de los logs aportados

- `gateway` reiniciaba con `ImportError: cannot import name 'ExecutionContext' from 'graphql.execution'`.
- `strawberry-graphql==0.266.0` utiliza la clase `ExecutionContext`. A partir de graphql-core 3.3 pasó a llamarse `Executor`; el cambio rompe esta versión de Strawberry.
- El `graphql-core` original no estaba fijado, por lo que una nueva construcción de imagen pudo resolver la rama 3.3 incompatible.
- El error `curl: (7) ... localhost:8001` es consecuencia del reinicio del gateway, no de una avería del frontend o DynamoDB.
- Floci mostraba advertencias de acceso a `/var/run/docker.sock` para servicios AWS que ejecutan contenedores. Es **independiente del fallo GraphQL**: DynamoDB y S3 pueden funcionar sin ese socket. Por seguridad no se monta automáticamente el socket.

## Cambios realizados

1. Dependencia `graphql-core==3.2.13` explícita junto a Strawberry 0.266.0.
2. Verificación de importación GraphQL **durante el build de Docker**.
3. Prueba de regresión `tests/test_gateway_import.py`, incluida en CI.
4. `scripts/launch.sh` verifica el endpoint `/health` y reporta logs al fallar.
5. `scripts/demo.sh` comprueba salud, errores GraphQL, busca un conector libre y restaura la flag tras ejecutarse.

## Reparar tu instalación Linux sin borrar datos

Desde la carpeta `AegisVolt` del ZIP corregido:

```bash
chmod +x scripts/*.sh
./scripts/launch.sh test
curl -fsS http://localhost:8001/health
./scripts/demo.sh
```

**Importante:** no uses `docker compose down -v`: elimina los volúmenes persistentes de Floci.

Si Docker conserva una imagen vieja:

```bash
APP_ENV=test AWS_PORT=4567 API_PORT=8001 WEB_PORT=8081 docker compose -p aegisvolt-test build --no-cache gateway
./scripts/launch.sh test
```

También puedes comprobar manualmente la dependencia real:

```bash
docker compose -p aegisvolt-test exec gateway python -c 'import graphql; from graphql.execution import ExecutionContext; print(graphql.__version__)'
```

La corrección no necesita credenciales de AWS; usa Floci local. Solo se pudo validar estáticamente el código en el entorno donde se preparó el ZIP, sin un daemon Docker disponible.
