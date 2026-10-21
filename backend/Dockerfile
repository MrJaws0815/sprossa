FROM python:3.13-slim

WORKDIR /app

# System-Deps für psycopg2 / asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten (separater Layer für Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code
COPY app/ ./app/

# Port für uvicorn
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]