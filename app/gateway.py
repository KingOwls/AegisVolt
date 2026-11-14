import os
import uuid
from typing import Optional
import httpx
import strawberry
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from .common import *

STATION=os.getenv('STATION_URL','http://localhost:8001')
BILLING=os.getenv('BILLING_URL','http://localhost:8002')
ENERGY=os.getenv('ENERGY_URL','http://localhost:8003')

async def call(base,path,payload=None):
    async with httpx.AsyncClient(timeout=12.0) as c:
        try: r=await c.request('POST' if payload is not None else 'GET',f'{base}{path}',json=payload)
        except httpx.RequestError as e: raise RuntimeError(f'Servicio no disponible: {e}')
        if r.status_code>=400: raise RuntimeError(f'{r.status_code}: {r.text}')
        return r.json()

def flag_value(k):
    row=get('flags',k)
    return bool(row.get('enabled')) if row else False

def price(): return 15.0 if flag_value('ENABLE_DYNAMIC_SURGE_PRICING') else 10.0

async def saga(connector_id,fleet_id):
    saga_id=str(uuid.uuid4())
    amount=price()
    record={'pk':saga_id,'connector_id':connector_id,'fleet_id':fleet_id,
            'amount':Decimal(str(amount)),'status':'STARTED','events':['STARTED'],'created_at':now()}
    put('sagas',record,'attribute_not_exists(pk)')
    reserve={'saga_id':saga_id,'connector_id':connector_id,'fleet_id':fleet_id}
    payment={'saga_id':saga_id,'fleet_id':fleet_id,'amount':amount}
    reserved=False
    charged=False
    try:
        await call(STATION,'/reserve',reserve)
        reserved=True
        update('sagas',saga_id,'SET #s=:s, events=list_append(events,:e)',{':s':'RESERVED',':e':['RESERVED']},names={'#s':'status'})
        await call(BILLING,'/charge',payment)
        charged=True
        update('sagas',saga_id,'SET #s=:s, events=list_append(events,:e)',{':s':'CHARGED',':e':['CHARGED']},names={'#s':'status'})
        await call(ENERGY,'/activate',{'saga_id':saga_id,'connector_id':connector_id,
                            'simulate_fault':flag_value('SIMULATE_CHARGER_HARDWARE_FAULT')})
        update('sagas',saga_id,'SET #s=:s, events=list_append(events,:e)',{':s':'COMPLETED',':e':['ACTIVATED']},names={'#s':'status'})
        log('gateway','SAGA_COMPLETED',saga_id)
    except Exception as exc:
        reason=str(exc)[:400]
        log('gateway','SAGA_FAILED',saga_id,error=reason)
        update('sagas',saga_id,'SET #s=:s, #err=:error, events=list_append(events,:e)',
             {':s':'COMPENSATING',':error':reason,':e':['COMPENSATING']},names={'#s':'status','#err':'error'})
        errors=[]
        if charged:
            try:
                await call(BILLING,'/refund',payment)
                update('sagas',saga_id,'SET events=list_append(events,:e)',{':e':['REFUNDED']})
            except Exception as e:errors.append('refund: '+str(e))
        if reserved:
            try:
                await call(STATION,'/release',reserve)
                update('sagas',saga_id,'SET events=list_append(events,:e)',{':e':['RELEASED']})
            except Exception as e:errors.append('release: '+str(e))
        status='COMPENSATION_FAILED' if errors else 'COMPENSATED'
        update('sagas',saga_id,'SET #s=:s, compensation_errors=:errs',
              {':s':status,':errs':errors},names={'#s':'status'})
        log('gateway',status,saga_id,errors=errors)
    return as_float(get('sagas',saga_id))

@strawberry.type
class Connector:
    id:str
    status:str
    saga_id:Optional[str]
@strawberry.type
class Wallet:
    fleet_id:str
    balance:float
@strawberry.type
class Flag:
    key:str
    enabled:bool
@strawberry.type
class Transaction:
    id:str
    status:str
    connector_id:str
    fleet_id:str
    amount:float
    events:list[str]
    error:Optional[str]
@strawberry.type
class Telemetry:
    id:str
    connector_id:str
    status:str
    power_kw:float
    energy_kwh:float

@strawberry.type
class Query:
    @strawberry.field
    async def connectors(self)->list[Connector]:
        rows=await call(STATION,'/connectors')
        return [Connector(id=r['pk'],status=r['status'],saga_id=r.get('saga_id')) for r in rows]
    @strawberry.field
    async def wallets(self)->list[Wallet]:
        rows=await call(BILLING,'/wallets')
        return [Wallet(fleet_id=r['pk'],balance=r['balance']) for r in rows]
    @strawberry.field
    def flags(self)->list[Flag]:return [Flag(key=r['pk'],enabled=r['enabled']) for r in scan('flags')]
    @strawberry.field
    def transactions(self)->list[Transaction]:
        return [Transaction(id=r['pk'],status=r['status'],connector_id=r['connector_id'],
             fleet_id=r['fleet_id'],amount=float(r['amount']),events=r.get('events',[]),error=r.get('error'))
             for r in scan('sagas')]
    @strawberry.field
    async def telemetry(self)->list[Telemetry]:
        rows=await call(ENERGY,'/telemetry')
        return [Telemetry(id=r['pk'],connector_id=r['connector_id'],status=r['status'],
             power_kw=r['power_kw'],energy_kwh=r['energy_kwh']) for r in rows]
    @strawberry.field
    def environment(self)->str:return ENV

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def reserve_and_activate(self,connector_id:str,fleet_id:str)->Transaction:
        r=await saga(connector_id,fleet_id)
        return Transaction(id=r['pk'],status=r['status'],connector_id=r['connector_id'],fleet_id=r['fleet_id'],
                           amount=float(r['amount']),events=r.get('events',[]),error=r.get('error'))
    @strawberry.mutation
    def set_flag(self,key:str,enabled:bool)->Flag:
        if key not in ('ENABLE_DYNAMIC_SURGE_PRICING','ENABLE_FAST_CHARGE_BOOST','SIMULATE_CHARGER_HARDWARE_FAULT'):
            raise ValueError('Flag no reconocida')
        update('flags',key,'SET enabled=:value, updated_at=:now',
               {':value':enabled,':now':now()},'attribute_exists(pk)')
        log('gateway','FLAG_CHANGED',None,key=key,enabled=enabled)
        return Flag(key=key,enabled=enabled)

schema=strawberry.Schema(query=Query,mutation=Mutation)
app=FastAPI(title='AegisVolt GraphQL Gateway')
app.add_middleware(CORSMiddleware,allow_origin_regex=r'http://(localhost|127\.0\.0\.1):808[0-2]',allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
app.include_router(GraphQLRouter(schema),prefix='/graphql')
@app.get('/health')
async def health(): return {'ok':True,'service':'gateway','env':ENV}
