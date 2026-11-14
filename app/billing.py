from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from decimal import Decimal
from botocore.exceptions import ClientError
from .common import *
app=FastAPI(title='Billing Wallet Service')
class Payment(BaseModel):
    saga_id:str
    fleet_id:str
    amount:float=Field(gt=0)
@app.get('/health')
def health():return {'ok':True,'service':'billing','env':ENV}
@app.get('/wallets')
def wallets():return as_float(scan('wallets'))
@app.get('/payments')
def payments():return as_float(scan('payments'))
@app.post('/charge')
def charge(body:Payment):
    original=get('payments',body.saga_id)
    if original:
      if original['fleet_id']==body.fleet_id and float(original['amount'])==body.amount and original['status']=='CHARGED':
        return {'status':'CHARGED','idempotent':True}
      raise HTTPException(409,'SAGA ya tiene un registro de cobro')
    amount=Decimal(str(body.amount))
    client=raw_dynamo_client()
    try:
      client.transact_write_items(TransactItems=[
       {'Update':{'TableName':name('wallets'),'Key':{'pk':{'S':body.fleet_id}},
          'UpdateExpression':'SET balance = balance - :amount',
          'ConditionExpression':'attribute_exists(pk) AND balance >= :amount',
          'ExpressionAttributeValues':{':amount':{'N':str(amount)}}}},
       {'Put':{'TableName':name('payments'),
          'Item':{'pk':{'S':body.saga_id},'fleet_id':{'S':body.fleet_id},'amount':{'N':str(amount)},'status':{'S':'CHARGED'},'created_at':{'S':now()}},
          'ConditionExpression':'attribute_not_exists(pk)'}}])
    except ClientError as e:
      if e.response['Error']['Code'] in ('TransactionCanceledException','ConditionalCheckFailedException'):
        raise HTTPException(409,'Fondos insuficientes o SAGA duplicada')
      raise
    log('billing','CHARGED',body.saga_id,amount=body.amount)
    return {'status':'CHARGED','amount':body.amount}
@app.post('/refund')
def refund(body:Payment):
    payment=get('payments',body.saga_id)
    if not payment: raise HTTPException(404,'Cobro inexistente')
    if payment['fleet_id']!=body.fleet_id or float(payment['amount'])!=body.amount:
      raise HTTPException(409,'Datos de reembolso incompatibles')
    if payment['status']=='REFUNDED': return {'status':'REFUNDED','idempotent':True}
    if payment['status']!='CHARGED': raise HTTPException(409,'Estado de pago inválido')
    amount=Decimal(str(body.amount))
    try:
      raw_dynamo_client().transact_write_items(TransactItems=[
        {'Update':{'TableName':name('payments'),'Key':{'pk':{'S':body.saga_id}},
          'UpdateExpression':'SET #s=:new, refunded_at=:now',
          'ConditionExpression':'#s=:old',
          'ExpressionAttributeNames':{'#s':'status'},
          'ExpressionAttributeValues':{':new':{'S':'REFUNDED'},':old':{'S':'CHARGED'},':now':{'S':now()}}}},
        {'Update':{'TableName':name('wallets'),'Key':{'pk':{'S':body.fleet_id}},
          'UpdateExpression':'SET balance = balance + :amount',
          'ConditionExpression':'attribute_exists(pk)',
          'ExpressionAttributeValues':{':amount':{'N':str(amount)}}}}])
    except ClientError as e: raise_http(e)
    log('billing','REFUNDED',body.saga_id,amount=body.amount)
    return {'status':'REFUNDED'}
