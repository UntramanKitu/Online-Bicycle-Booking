FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir \
    "fastapi>=0.139.2" \
    "psycopg[binary]>=3.2.13" \
    "pydantic-settings>=2.10.1" \
    "sqlalchemy>=2.0.41" \
    "uvicorn>=0.51.0"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
