from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .common import *
app=FastAPI(title='Energy Dispatch Service')
class Activate(BaseModel):
    saga_id:str
    connector_id:str
    simulate_fault:bool=False
@app.get('/health')
def health():return {'ok':True,'service':'energy','env':ENV}
@app.get('/telemetry')
def telemetry():return as_float(scan('dispatch'))
@app.post('/activate')
def activate(body:Activate):
    item=get('dispatch',body.saga_id)
    if item:
      if item['connector_id']==body.connector_id and item['status']=='ACTIVE':return {'status':'ACTIVE','idempotent':True}
      raise HTTPException(409,'Sesión previamente registrada')
    if body.simulate_fault:
       log('energy','HARDWARE_FAULT',body.saga_id,connector_id=body.connector_id)
       raise HTTPException(503,'SIMULATED_CHARGER_HARDWARE_FAULT')
    try:
      put('dispatch',{'pk':body.saga_id,'connector_id':body.connector_id,'status':'ACTIVE',
          'power_kw':Decimal('50'),'energy_kwh':Decimal('0'),'started_at':now()},'attribute_not_exists(pk)')
    except ClientError as e: raise_http(e)
    log('energy','ACTIVATED',body.saga_id,connector_id=body.connector_id)
    return {'status':'ACTIVE','power_kw':50}
