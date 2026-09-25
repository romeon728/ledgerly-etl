FROM python:3.12-slim

# Install libpq for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first for efficient caching
COPY pyproject.toml .
COPY src/ src/

# Install the package and dependencies
RUN pip install --no-cache-dir .

EXPOSE 8501

CMD ["streamlit", "run", "src/ledgerly/app.py", "--server.address=0.0.0.0"]