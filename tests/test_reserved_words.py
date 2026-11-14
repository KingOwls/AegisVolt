"""Regression: DynamoDB reserves the attribute name `error`."""
from unittest.mock import patch
import pytest

@pytest.mark.asyncio
async def test_failed_saga_escapes_error_attribute():
    from app.gateway import saga
    updates = []
    calls = []
    async def fake_call(base, path, payload=None):
        calls.append(path)
        if path == '/activate':
            raise RuntimeError('SIMULATED_CHARGER_HARDWARE_FAULT')
        return {'ok': True}
    def fake_update(suffix, pk, expr, values, condition=None, names=None):
        updates.append((expr, names or {}))
    with patch('app.gateway.call', new=fake_call), \
         patch('app.gateway.price', return_value=10.0), \
         patch('app.gateway.flag_value', return_value=True), \
         patch('app.gateway.put'), \
         patch('app.gateway.update', side_effect=fake_update), \
         patch('app.gateway.log'), \
         patch('app.gateway.get', return_value={
             'pk': 'test','status': 'COMPENSATED','connector_id': 'BAY-01',
             'fleet_id': 'FLEET-DEMO','amount': 10,'events': ['REFUNDED','RELEASED']
         }):
        result = await saga('BAY-01', 'FLEET-DEMO')
    assert result['status'] == 'COMPENSATED'
    assert calls == ['/reserve', '/charge', '/activate', '/refund', '/release']
    error_updates = [(expr, names) for expr, names in updates if '#err' in expr]
    assert len(error_updates) == 1
    assert error_updates[0][1]['#err'] == 'error'
    assert not any(' error=' in expr for expr, _ in updates)
