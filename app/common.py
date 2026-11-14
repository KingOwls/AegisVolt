import json
import logging
import os
import time
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from functools import lru_cache
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException

ENV = os.getenv('APP_ENV', 'dev')
ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
PREFIX = f'aegisvolt-{ENV}'

def now(): return datetime.now(timezone.utc).isoformat()
def name(suffix): return f'{PREFIX}-{suffix}'

@lru_cache(maxsize=1)
def dynamo():
    return boto3.resource('dynamodb',endpoint_url=ENDPOINT,region_name=REGION,
       aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID','test'),
       aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY','test'),
       config=Config(retries={'max_attempts':3,'mode':'standard'}))

def raw_dynamo_client():
    return boto3.client('dynamodb',endpoint_url=ENDPOINT,region_name=REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID','test'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY','test'))

def table(suffix): return dynamo().Table(name(suffix))
def get(suffix,pk): return table(suffix).get_item(Key={'pk':pk},ConsistentRead=True).get('Item')
def put(suffix,obj,condition=None):
    kw={'Item':obj}
    if condition: kw['ConditionExpression']=condition
    return table(suffix).put_item(**kw)
def update(suffix,pk,expr,values,condition=None,names=None):
    kw={'Key':{'pk':pk},'UpdateExpression':expr,'ExpressionAttributeValues':values,'ReturnValues':'ALL_NEW'}
    if condition: kw['ConditionExpression']=condition
    if names: kw['ExpressionAttributeNames']=names
    return table(suffix).update_item(**kw)['Attributes']
def scan(suffix):
    t=table(suffix); r=t.scan(); items=r.get('Items',[])
    while 'LastEvaluatedKey' in r:
        r=t.scan(ExclusiveStartKey=r['LastEvaluatedKey']);items+=r.get('Items',[])
    return items

def log(service,event,correlation_id=None,**kw):
    data={'timestamp':now(),'env':ENV,'service':service,'event':event,'correlation_id':correlation_id,**kw}
    logging.info(json.dumps(data,default=str,ensure_ascii=False))
    if os.getenv('CLOUDWATCH_ENABLED','true').lower()=='true':
      try:
        client=boto3.client('logs',endpoint_url=ENDPOINT,region_name=REGION,
                            aws_access_key_id='test',aws_secret_access_key='test')
        group=f'/aegisvolt/{ENV}/{service}'
        stream='application'
        try: client.create_log_group(logGroupName=group)
        except ClientError as e:
          if e.response['Error']['Code']!='ResourceAlreadyExistsException': raise
        try: client.create_log_stream(logGroupName=group,logStreamName=stream)
        except ClientError as e:
          if e.response['Error']['Code']!='ResourceAlreadyExistsException': raise
        client.put_log_events(logGroupName=group,logStreamName=stream,
          logEvents=[{'timestamp':int(time.time()*1000),'message':json.dumps(data,default=str)}])
      except Exception as e: logging.warning('CloudWatch unavailable: %s',str(e))

def raise_http(exc):
    if isinstance(exc,ClientError) and exc.response['Error']['Code']=='ConditionalCheckFailedException':
        raise HTTPException(409,'Conflicto de estado / solicitud duplicada')
    raise exc

def as_float(item):
    if isinstance(item,dict): return {k:as_float(v) for k,v in item.items()}
    if isinstance(item,list): return [as_float(v) for v in item]
    if isinstance(item,Decimal): return float(item)
    return item
