import os
import pytest
import httpx

@pytest.mark.skipif(not os.getenv('AEGIS_E2E'),reason='Requires test environment and resets flag')
@pytest.mark.asyncio
async def test_hardware_fault_compensates():
    endpoint=os.getenv('AEGIS_API','http://localhost:8001/graphql')
    async with httpx.AsyncClient(timeout=15) as c:
      async def q(query):
        r=await c.post(endpoint,json={'query':query});r.raise_for_status();payload=r.json()
        assert 'errors' not in payload, payload
        return payload['data']
      await q('mutation{setFlag(key:"SIMULATE_CHARGER_HARDWARE_FAULT",enabled:true){enabled}}')
      try:
        connectors=(await q('{connectors{id status}}'))['connectors']
        available=next(x['id'] for x in connectors if x['status']=='AVAILABLE')
        before=(await q('{wallets{fleetId balance}}'))['wallets'][0]['balance']
        result=await q(f'mutation{{reserveAndActivate(connectorId:"{available}",fleetId:"FLEET-DEMO"){{status events}}}}')
        assert result['reserveAndActivate']['status']=='COMPENSATED'
        assert result['reserveAndActivate']['events'][-2:]==['REFUNDED','RELEASED']
        after=(await q('{wallets{fleetId balance} connectors{id status}}'))
        assert after['wallets'][0]['balance']==before
        assert next(x for x in after['connectors'] if x['id']==available)['status']=='AVAILABLE'
      finally:
        await q('mutation{setFlag(key:"SIMULATE_CHARGER_HARDWARE_FAULT",enabled:false){enabled}}')
