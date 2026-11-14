"""Create resources for local quickstart; Terraform remains IaC source for evaluated infrastructure."""
import os
import sys
from botocore.exceptions import ClientError
from app.common import *

def main():
  client=raw_dynamo_client()
  for suffix in ['reservations','wallets','payments','dispatch','sagas','flags']:
    n=name(suffix)
    try:
      client.create_table(TableName=n,KeySchema=[{'AttributeName':'pk','KeyType':'HASH'}],
          AttributeDefinitions=[{'AttributeName':'pk','AttributeType':'S'}],BillingMode='PAY_PER_REQUEST')
      print('created',n)
    except ClientError as e:
      if e.response['Error']['Code']!='ResourceInUseException': raise
  for id in ['BAY-01','BAY-02','BAY-03']:
    try: put('reservations',{'pk':id,'status':'AVAILABLE','updated_at':now()},'attribute_not_exists(pk)')
    except ClientError as e:
      if e.response['Error']['Code']!='ConditionalCheckFailedException': raise
  try:put('wallets',{'pk':'FLEET-DEMO','balance':Decimal('100')},'attribute_not_exists(pk)')
  except ClientError as e:
    if e.response['Error']['Code']!='ConditionalCheckFailedException':raise
  defaults={'ENABLE_DYNAMIC_SURGE_PRICING':ENV!='prod','ENABLE_FAST_CHARGE_BOOST':ENV=='dev',
            'SIMULATE_CHARGER_HARDWARE_FAULT':False}
  for k,v in defaults.items():
    try:put('flags',{'pk':k,'enabled':v,'updated_at':now()},'attribute_not_exists(pk)')
    except ClientError as e:
      if e.response['Error']['Code']!='ConditionalCheckFailedException': raise
  print(f'bootstrap complete: {ENV} ({ENDPOINT})')
if __name__=='__main__':main()
