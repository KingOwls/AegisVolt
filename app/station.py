from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .common import *
app=FastAPI(title='Station Reservation Service')
class Request(BaseModel):
    saga_id:str
    connector_id:str
    fleet_id:str
@app.get('/health')
def health(): return {'ok':True,'service':'station','env':ENV}
@app.get('/connectors')
def connectors(): return as_float(scan('reservations'))
@app.post('/reserve')
def reserve(body:Request):
    pk=body.connector_id
    try:
      item=update('reservations',pk,'SET #s=:reserved, saga_id=:id, fleet_id=:fleet, updated_at=:now',
          {':reserved':'RESERVED',':available':'AVAILABLE',':id':body.saga_id,':fleet':body.fleet_id,':now':now()},
          'attribute_exists(pk) AND #s=:available',{'#s':'status'})
      log('station','RESERVED',body.saga_id,connector_id=pk)
      return as_float(item)
    except ClientError as e: raise_http(e)
@app.post('/release')
def release(body:Request):
    item=get('reservations',body.connector_id)
    if not item: raise HTTPException(404,'Conector inexistente')
    if item.get('status')=='AVAILABLE':
        if item.get('last_saga_id')==body.saga_id: return {'status':'AVAILABLE','idempotent':True}
        raise HTTPException(409,'El conector fue liberado por otra transacción')
    if item.get('saga_id')!=body.saga_id: raise HTTPException(409,'La reserva pertenece a otra SAGA')
    try:
      result=update('reservations',body.connector_id,
         'SET #s=:available, last_saga_id=:id, updated_at=:now REMOVE saga_id, fleet_id',
         {':available':'AVAILABLE',':id':body.saga_id,':now':now(),':reserved':'RESERVED'},
         '#s=:reserved AND saga_id=:id',{'#s':'status'})
      log('station','RELEASED',body.saga_id,connector_id=body.connector_id)
      return as_float(result)
    except ClientError as e: raise_http(e)
