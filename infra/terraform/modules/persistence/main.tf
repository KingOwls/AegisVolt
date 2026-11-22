variable "prefix" {
  type = string
}

variable "tables" {
  type = set(string)
}

resource "aws_dynamodb_table" "service" {
  for_each = var.tables

  name         = "${var.prefix}-${each.value}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"

  attribute {
    name = "pk"
    type = "S"
  }

  tags = {
    Project = "AegisVolt"
    Service = each.value
  }
}

output "table_names" {
  value = {
    for k, v in aws_dynamodb_table.service :
    k => v.name
  }
}
