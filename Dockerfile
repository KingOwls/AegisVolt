FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from graphql.execution import ExecutionContext; import strawberry; print('GraphQL dependencies OK')"
COPY app ./app
COPY scripts ./scripts
COPY observability ./observability
RUN useradd --uid 10001 --create-home aegis
USER aegis
EXPOSE 8000
CMD ["uvicorn","app.gateway:app","--host","0.0.0.0","--port","8000"]
