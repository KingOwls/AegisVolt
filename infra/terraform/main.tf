locals {
  env      = terraform.workspace
  prefix   = "aegisvolt-${local.env}"
  tables   = toset(["reservations", "wallets", "payments", "dispatch", "sagas", "flags"])
  services = toset(["gateway", "station", "billing", "energy"])
}
module "persistence" {
  source = "./modules/persistence"
  prefix = local.prefix
  tables = local.tables
}
module "network" {
  count                       = var.enable_network ? 1 : 0
  source                      = "./modules/network"
  prefix                      = local.prefix
  region                      = var.region
  dynamodb_interface_endpoint = var.local_emulation
}
resource "aws_cloudwatch_log_group" "service" {
  for_each          = local.services
  name              = "/aegisvolt/${local.env}/${each.key}"
  retention_in_days = 7
}
output "workspace" { value = terraform.workspace }
output "table_names" { value = module.persistence.table_names }
output "vpc_id" { value = var.enable_network ? module.network[0].vpc_id : "Emulated-local: no VPC path enforced" }
