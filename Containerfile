FROM python:3.12-slim

WORKDIR /app

# Copy project definition and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install application and dependencies in a single step
RUN pip install -e .

EXPOSE 8501

CMD ["streamlit", "run", "src/ledgerly/app.py", "--server.address=0.0.0.0", "--server.port=8501"]