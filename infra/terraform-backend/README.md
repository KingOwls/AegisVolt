# Backend S3 remoto y versionado (paso previo a `terraform init`)

El bucket **no puede crearse desde el mismo estado remoto que depende de él**. Primero use AWS CLI con Floci (ej. `./scripts/aws-local.sh dev ...` desde la raíz):

```bash
./scripts/aws-local.sh dev s3api create-bucket --bucket aegisvolt-tfstate-local
./scripts/aws-local.sh dev s3api put-bucket-versioning --bucket aegisvolt-tfstate-local --versioning-configuration Status=Enabled
./scripts/aws-local.sh dev s3api get-bucket-versioning --bucket aegisvolt-tfstate-local
```

Para un backend separado por ambiente, utilice **una instancia Floci central y persistente** que permanezca viva durante todos los despliegues y configure un único backend `-backend-config=endpoint=http://localhost:4566`. El script `terraform-local.sh` usa estado LOCAL para facilitar la práctica rápida, **NO demuestra** esta rúbrica. Para demostrar workspaces y tfstate S3:

```bash
cd infra/terraform
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1
terraform init -reconfigure \
  -backend-config='bucket=aegisvolt-tfstate-local' \
  -backend-config='key=aegisvolt/terraform.tfstate' \
  -backend-config='region=us-east-1' \
  -backend-config='use_path_style=true' \
  -backend-config='skip_credentials_validation=true' \
  -backend-config='skip_metadata_api_check=true' \
  -backend-config='skip_requesting_account_id=true' \
  -backend-config='endpoints={s3="http://localhost:4566"}'
terraform workspace new dev || terraform workspace select dev
terraform plan -var='endpoint=http://localhost:4566' -var='enable_network=false'
terraform apply -var='endpoint=http://localhost:4566' -var='enable_network=false'
```

Backend remoto central y **datos por ambiente**: para tres ambientes en un solo Floci, ejecutar **una sola instancia** y usar workspaces para recursos `aegisvolt-dev-*`, `aegisvolt-test-*`, `aegisvolt-prod-*`. El Compose rápido ejecuta Floci independiente por ambiente para aislamiento operativo; no confunda esos dos perfiles. S3 backend no es seguro para concurrencia sin locking compatible: nunca aplique dos veces en paralelo. En AWS real habilite `use_lockfile=true` y permisos de bloqueo.

Recuperación: use `aws s3api list-object-versions --bucket aegisvolt-tfstate-local --prefix env:/dev/aegisvolt/terraform.tfstate` y restaure primero copiando la versión que elija a una ruta de respaldo; verifique el hash y aplique con mantenimiento programado. Nunca borre versiones originales.
