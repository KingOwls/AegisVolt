# Diagnóstico de los ambientes y recuperación de una SAGA previa

## Qué muestran los registros

- El nuevo flujo en `test` terminó correctamente con `COMPENSATED` e incluyó `REFUNDED` y `RELEASED`.
- La SAGA anterior `9837aa2b-5d0c-442f-860a-1e9cb981ccc4` continúa en `CHARGED` y `BAY-01` permanece `RESERVED`. Se observa saldo 85 para `FLEET-DEMO`. Debe inspeccionarse la transacción antes de compensarla.
- El comando `python -m scripts.recover_sagas` falló **antes** de `./scripts/launch.sh test` porque la imagen antigua aún no contenía el módulo. Tras reconstruir los servicios debería estar disponible.
- `http://localhost:8082` sirve el HTML del frontend de `prod`, pero **no confirma** que la API `http://localhost:8002/graphql` esté disponible. Error `ERR_CONNECTION_REFUSED` significa que no se estableció conexión TCP con el puerto 8002. `Floci` en 4568 no es el gateway GraphQL.

## Diagnosticar test y prod

Desde la carpeta `AegisVolt`:

```bash
chmod +x scripts/*.sh
./scripts/status.sh test
./scripts/status.sh prod
./scripts/launch.sh prod
curl -fsS http://localhost:8002/health
./scripts/status.sh prod
```

Si prod no inicia, inspeccionar `docker compose -p aegisvolt-prod logs --tail=100 gateway init floci` y verificar el mapeo `8002:8000`. Para la UI de test usar `http://localhost:8081` y GraphQL `http://localhost:8001/graphql`. Para la UI de prod usar `http://localhost:8082` y GraphQL `http://localhost:8002/graphql`.

## Reparar transacción anterior, sin tocar volúmenes

```bash
./scripts/launch.sh test
./scripts/recover.sh test
./scripts/recover.sh test --saga-id 9837aa2b-5d0c-442f-860a-1e9cb981ccc4
```

La vista previa identifica si el despacho está activo, si hay un cobro vigente y si la SAGA es propietaria de la reserva. **Comprobar los datos antes de aprobar el reembolso**. Solo si se trata de la SAGA antigua atascada, no de una carga realmente activa:

```bash
./scripts/recover.sh test --saga-id 9837aa2b-5d0c-442f-860a-1e9cb981ccc4 --apply
./scripts/recover.sh test
./scripts/demo.sh
```

Se espera que BAY-01 quede `AVAILABLE` y el saldo vuelva a 100 tras la recuperación, **si** el cobro de 15 pertenecía a esa SAGA y no hubo otras operaciones. El script no modifica ningún dato sin `--apply`; se niega a reembolsar una sesión con despacho `ACTIVE`.

**No usar** `docker compose down -v`. Evitar gestionar volúmenes o registros de DynamoDB manualmente para ocultar inconsistencias. No usar `--apply` sobre `prod` sin una revisión de la transacción.
