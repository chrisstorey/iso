# This is the Dockerfile for the backend application.
FROM python:3.9-slim

WORKDIR /app

# Install OS dependencies for shapely (GEOS) and psycopg2 (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libpq-dev \
    # build-essential might be needed for some packages if they compile C extensions
    # build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
