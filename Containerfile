# Changed from python:3.12-slim
FROM docker.io/library/python:3.12-slim

# Install system dependencies for PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy packaging details & source code
COPY pyproject.toml .
COPY src/ src/

# Install application dependencies directly from pyproject.toml
RUN pip install --no-cache-dir .

EXPOSE 8501

CMD ["streamlit", "run", "src/ledgerly/app.py", "--server.address=0.0.0.0", "--server.port=8501"]