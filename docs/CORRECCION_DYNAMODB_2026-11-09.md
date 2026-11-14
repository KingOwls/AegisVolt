# Corrección: palabra reservada DynamoDB en SAGA

## Diagnóstico

Después de corregir Strawberry, la mutación `reserveAndActivate` llegó al paso de compensación, pero `UpdateItem` devolvió:

`ValidationException: Invalid UpdateExpression: Attribute name is a reserved keyword; reserved word: error`

El gateway escribía `SET #s=:s, error=:error, ...`. El identificador `error` es reservado en DynamoDB y debe escaparse con `ExpressionAttributeNames`.

## Corrección aplicada

Ahora se utiliza `SET #s=:s, #err=:error, ...` con `{'#s':'status','#err':'error'}`. Se añadió prueba de regresión `tests/test_reserved_words.py`.

## Ejecución en Linux sin eliminar volúmenes

```bash
./scripts/launch.sh test
curl -fsS http://localhost:8001/health
./scripts/demo.sh
```

Para inspeccionar transacciones que quedaron pendientes por el error anterior:

```bash
docker compose -p aegisvolt-test exec gateway python -m scripts.recover_sagas
```

Para ver exactamente qué haría una reparación de UNA SAGA:

```bash
docker compose -p aegisvolt-test exec gateway python -m scripts.recover_sagas --saga-id UUID
```

Después de verificar el identificador, que no hay despacho activo y que los importes son correctos, solicitar explícitamente la reparación:

```bash
docker compose -p aegisvolt-test exec gateway python -m scripts.recover_sagas --saga-id UUID --apply
```

La recuperación rechaza sesiones con despacho `ACTIVE`. Si hay otras inconsistencias o compensaciones fallidas, no forzar cambios directos en la tabla sin verificar el estado. Evitar `docker compose down -v` para conservar DynamoDB persistido en Floci.

Nota: este proyecto es un prototipo académico. Para producción haría falta un proceso de recuperación automática confiable, deduplicación y reconciliación de estados con bloqueos/condiciones transaccionales.
