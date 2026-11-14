import os
import pytest
import httpx

@pytest.mark.skipif(not os.getenv('AEGIS_INTEGRATION'),reason='Requires running Docker Compose')
@pytest.mark.asyncio
async def test_graphql_and_dynamodb():
    endpoint=os.getenv('AEGIS_API','http://localhost:8000/graphql')
    async with httpx.AsyncClient(timeout=10) as c:
        r=await c.post(endpoint,json={'query':'{connectors{id status} wallets{fleetId balance} flags{key enabled}}'})
        assert r.status_code==200
        data=r.json()['data']
        assert len(data['connectors'])>=1
        assert len(data['wallets'])>=1
        assert len(data['flags'])==3
