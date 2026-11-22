"""Regression: strawberry/graphql-core compatibility broke gateway startup."""
def test_gateway_import_and_schema():
    from graphql.execution import ExecutionContext
    from app.gateway import app, schema
    assert ExecutionContext is not None
    assert schema._schema.query_type is not None
    assert any(route.path == "/health" for route in app.routes)
