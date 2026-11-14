variable "prefix" {type=string}
variable "region" {type=string}
data "aws_availability_zones" "available" {state="available"}
resource "aws_vpc" "main" {
 cidr_block="10.42.0.0/16"
 enable_dns_hostnames=true
 enable_dns_support=true
 tags={Name="${var.prefix}-vpc"}
}
resource "aws_internet_gateway" "igw" {
 vpc_id=aws_vpc.main.id
 tags={Name="${var.prefix}-igw"}
}
resource "aws_subnet" "public" {
 count=2
 vpc_id=aws_vpc.main.id
 cidr_block=cidrsubnet(aws_vpc.main.cidr_block,8,count.index)
 availability_zone=data.aws_availability_zones.available.names[count.index]
 map_public_ip_on_launch=true
 tags={Name="${var.prefix}-public-${count.index}"}
}
resource "aws_subnet" "private" {
 count=2
 vpc_id=aws_vpc.main.id
 cidr_block=cidrsubnet(aws_vpc.main.cidr_block,8,count.index+10)
 availability_zone=data.aws_availability_zones.available.names[count.index]
 tags={Name="${var.prefix}-private-${count.index}"}
}
resource "aws_route_table" "public" {vpc_id=aws_vpc.main.id}
resource "aws_route" "internet" {
 route_table_id=aws_route_table.public.id
 destination_cidr_block="0.0.0.0/0"
 gateway_id=aws_internet_gateway.igw.id
}
resource "aws_route_table_association" "public" {
 count=2;subnet_id=aws_subnet.public[count.index].id;route_table_id=aws_route_table.public.id
}
resource "aws_route_table" "private" {vpc_id=aws_vpc.main.id}
resource "aws_route_table_association" "private" {
 count=2;subnet_id=aws_subnet.private[count.index].id;route_table_id=aws_route_table.private.id
}
resource "aws_security_group" "endpoints" {
 name="${var.prefix}-vpce"
 vpc_id=aws_vpc.main.id
 ingress {from_port=443;to_port=443;protocol="tcp";cidr_blocks=[aws_vpc.main.cidr_block]}
 egress {from_port=0;to_port=0;protocol="-1";cidr_blocks=["0.0.0.0/0"]}
}
resource "aws_vpc_endpoint" "gateway" {
 for_each=toset(["s3","dynamodb"])
 vpc_id=aws_vpc.main.id
 service_name="com.amazonaws.${var.region}.${each.value}"
 vpc_endpoint_type="Gateway"
 route_table_ids=[aws_route_table.private.id]
}
resource "aws_vpc_endpoint" "interface" {
 for_each=toset(["execute-api","logs","monitoring"])
 vpc_id=aws_vpc.main.id
 service_name="com.amazonaws.${var.region}.${each.value}"
 vpc_endpoint_type="Interface"
 subnet_ids=aws_subnet.private[*].id
 security_group_ids=[aws_security_group.endpoints.id]
 private_dns_enabled=true
}
output "vpc_id" {value=aws_vpc.main.id}
output "private_subnets" {value=aws_subnet.private[*].id}
