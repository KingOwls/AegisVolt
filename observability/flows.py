import os
import httpx
from prefect import flow,task
from app.common import ENV,scan

@task(retries=2,retry_delay_seconds=3)
def audit_sagas():
    rows=scan('sagas')
    bad=[{'id':r['pk'],'status':r['status']} for r in rows if r['status'] in ('COMPENSATION_FAILED','COMPENSATING','STARTED','RESERVED','CHARGED')]
    return {'env':ENV,'total':len(rows),'at_risk':bad,'compensated':sum(r['status']=='COMPENSATED' for r in rows)}

@task(retries=2,retry_delay_seconds=3)
async def health():
    base=os.getenv('GATEWAY_HEALTH_URL','http://localhost:8000')
    async with httpx.AsyncClient(timeout=10) as c:
        r=await c.get(base+'/health');r.raise_for_status();return r.json()

@flow(name='aegisvolt-saga-health-audit',log_prints=True)
async def audit():
    h=await health(); report=audit_sagas();print({'health':h,'sagas':report})
    if report['at_risk']: print('ATTENTION: orphaned/pending sagas:',report['at_risk'])
    return {'health':h,'sagas':report}

if __name__=='__main__':
 import asyncio
 asyncio.run(audit())
