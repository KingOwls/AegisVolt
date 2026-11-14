"""Inspect or explicitly compensate a single stalled SAGA after application failure.

Run in gateway container:
  python -m scripts.recover_sagas                  # list unresolved transactions
  python -m scripts.recover_sagas --saga-id UUID    # preview one
  python -m scripts.recover_sagas --saga-id UUID --apply  # compensate one

Never compensates a session recorded ACTIVE in dispatch. Explicitly authorized
repair only; no background sweeping or automatic refunds.
"""
import argparse
import json
import asyncio
from app.common import get, scan, update, now, as_float
from app.gateway import call, STATION, BILLING

UNRESOLVED = {'STARTED', 'RESERVED', 'CHARGED', 'COMPENSATING', 'COMPENSATION_FAILED'}

async def repair(row, apply):
    sid = row['pk']
    dispatch = get('dispatch', sid)
    payment = get('payments', sid)
    connector = get('reservations', row['connector_id'])
    own_reservation = bool(connector and connector.get('status') == 'RESERVED' and connector.get('saga_id') == sid)
    charged = bool(payment and payment.get('status') == 'CHARGED')
    active = bool(dispatch and dispatch.get('status') == 'ACTIVE')
    plan = {'saga_id':sid,'state':row['status'],'charged':charged,
            'reservation_owned':own_reservation,'active_dispatch':active,
            'actions':(['REFUND'] if charged else []) + (['RELEASE'] if own_reservation else [])}
    print(json.dumps(plan,indent=2,ensure_ascii=False))
    if not apply: return
    if row['status'] not in UNRESOLVED: raise RuntimeError('SAGA not pending; refusing modification')
    if active: raise RuntimeError('Dispatch is ACTIVE; refusing to refund an active charging session')
    errors=[]
    # Safety first: compensate money, then reservation; both endpoints are idempotent.
    if charged:
        try:
            await call(BILLING,'/refund',{'saga_id':sid,'fleet_id':row['fleet_id'],'amount':float(row['amount'])})
            update('sagas',sid,'SET events=list_append(events,:e)',{':e':['REFUNDED_RECOVERY']})
        except Exception as e: errors.append('refund: '+str(e))
    if own_reservation:
        try:
            await call(STATION,'/release',{'saga_id':sid,'fleet_id':row['fleet_id'],'connector_id':row['connector_id']})
            update('sagas',sid,'SET events=list_append(events,:e)',{':e':['RELEASED_RECOVERY']})
        except Exception as e: errors.append('release: '+str(e))
    status = 'COMPENSATION_FAILED' if errors else 'COMPENSATED'
    update('sagas',sid,'SET #s=:s, compensation_errors=:err',
           {':s':status,':err':errors},names={'#s':'status'})
    print(json.dumps({'saga_id':sid,'status':status,'errors':errors},ensure_ascii=False))
    if errors: raise RuntimeError('Some compensations failed; investigate before retrying')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saga-id',help='Specific pending SAGA identifier')
    parser.add_argument('--apply',action='store_true',help='Perform compensation (requires --saga-id)')
    args=parser.parse_args()
    if args.apply and not args.saga_id: parser.error('--apply requires --saga-id')
    if args.saga_id:
        row=get('sagas',args.saga_id)
        if not row: parser.error('SAGA not found')
        asyncio.run(repair(row,args.apply))
    else:
        pending=[{'id':x['pk'],'status':x['status'],'connector':x['connector_id']} for x in scan('sagas') if x.get('status') in UNRESOLVED]
        print(json.dumps(pending,indent=2,ensure_ascii=False))
if __name__ == '__main__': main()
