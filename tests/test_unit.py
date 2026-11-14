from unittest.mock import patch,AsyncMock
import pytest
from fastapi import HTTPException
from app.gateway import price

@patch('app.gateway.flag_value',return_value=True)
def test_surge_pricing_enabled(flag):assert price()==15.0
@patch('app.gateway.flag_value',return_value=False)
def test_surge_pricing_disabled(flag):assert price()==10.0

@pytest.mark.asyncio
async def test_saga_rollback_order():
  from app.gateway import saga
  calls=[]
  async def fake_call(base,path,payload=None):
    calls.append(path)
    if path=='/activate':raise RuntimeError('fault')
    return {'ok':True}
  with patch('app.gateway.call',new=fake_call),\
       patch('app.gateway.price',return_value=10.0),\
       patch('app.gateway.flag_value',return_value=True),\
       patch('app.gateway.put'),\
       patch('app.gateway.update'),\
       patch('app.gateway.log'),\
       patch('app.gateway.get',return_value={'pk':'demo','status':'COMPENSATED','connector_id':'BAY-01','fleet_id':'FLEET-DEMO','amount':10,'events':['REFUNDED','RELEASED']}):
      result=await saga('BAY-01','FLEET-DEMO')
  assert calls==['/reserve','/charge','/activate','/refund','/release']
  assert result['status']=='COMPENSATED'

@pytest.mark.asyncio
async def test_saga_insufficient_funds_only_releases():
  from app.gateway import saga
  calls=[]
  async def fake_call(base,path,payload=None):
    calls.append(path)
    if path=='/charge':raise RuntimeError('insufficient')
    return {'ok':True}
  with patch('app.gateway.call',new=fake_call),patch('app.gateway.price',return_value=10.0),\
       patch('app.gateway.put'),patch('app.gateway.update'),patch('app.gateway.log'),\
       patch('app.gateway.get',return_value={'pk':'demo','status':'COMPENSATED'}):
    await saga('BAY-01','FLEET-DEMO')
  assert calls==['/reserve','/charge','/release']
