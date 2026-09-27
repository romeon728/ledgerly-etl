# 📊 Ledgerly

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Podman](https://img.shields.io/badge/Podman-4.9+-892CA0?style=flat&logo=podman&logoColor=white)](https://podman.io)

**Ledgerly** is a privacy-first, fully containerized personal finance ETL (Extract, Transform, Load) engine and analytics workspace. It processes raw financial export files, applies automated normalization and AI-assisted categorization, stores structured data in PostgreSQL, and provides an interactive Streamlit workspace for exploring transactions and spending trends.

---

## 🚀 App: How to Use

1. **📥 Upload Tab**: Drag and drop raw bank statement CSVs. Select your bank format and click **Run ETL Pipeline**. The `ETLRunner` handles extraction, normalization, and deduplication asynchronously.
2. **💳 Transactions Tab**: Query PostgreSQL live to inspect incoming records, filter by date ranges or categories, and search specific line items.
3. **📈 Dashboard Tab**: Explore visual spending breakdowns, category metrics, and monthly financial trends.
4. **⚙️ Fine-Tuning**: Adjust classification rules directly within the interface to retrain or refine merchant categorization without editing source code.

---

## 🌟 Features

* **Modular Streamlit Architecture**: Dedicated tab views (`Upload`, `Transactions`, `Dashboard`, `About`) organized in a clean `views/` directory.
* **Asynchronous Ingestion Pipeline**: Powered by `ETLRunner` to process, normalize, and load bank statement CSVs without locking the UI.
* **Local AI Categorization**: Integrates with a local vLLM inference server (e.g., Qwen2.5) to categorize ambiguous transactions while keeping sensitive financial data 100% on-device.
* **Containerized Microservices**: Orchestrated with Podman / Docker Compose using separate containers for the database (`ledgerly-db`) and application (`ledgerly-app`).
* **Instant Hot-Reloading**: Source code volume-mounted directly into the container for immediate browser UI refreshes during local development.

---

## ⚙️ How to Setup

### Prerequisites

* [Podman](https://podman.io) (or Docker) with `podman-compose` / `docker-compose`
* Python 3.12+ (optional, for local non-containerized setup)

### 1. Clone & Configure Environment

Copy the example environment file and configure your local settings:

```bash
cp .env.example .env
```

Ensure your `.env` contains the required database and local LLM configuration:

```env
# Database Configuration (Internal container network settings)
DB_HOST=db
DB_PORT=5432
DB_NAME=ledgerly_db
DB_USER=ledgerly
DB_PASSWORD=ledgerly_local_sec_pass

# Local vLLM Inference Engine (Optional)
VLLM_BASE_URL=[http://127.0.0.1:8000/v1](http://127.0.0.1:8000/v1)
VLLM_MODEL_NAME=Qwen/Qwen2.5-3B-Instruct-AWQ
```

### 2. Enable Hot-Reloading (Recommended for Development)

In your `docker-compose.yml` (or `podman-compose.yaml`), ensure the source directory is bind-mounted under the `app` service:

```yaml
services:
  app:
    build: .
    container_name: ledgerly-app
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./src:/app/src
    depends_on:
      - db
```

### 3. Build & Launch

Spin up the container stack:

```bash
podman compose up -d --build
```

Access the Streamlit application at **`http://localhost:8501`**.

---

## 🛠️ Development & Debugging

### Quick Application Restart

If you update environment variables or package configuration, run the dedicated restart script to cleanly rebuild the app container without tearing down the database:

```bash
./scripts/restart_app.sh
```

### Common Issues & Troubleshooting

| Error / Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `psycopg2.OperationalError: connection ... refused` | App attempting to connect to `localhost` or wrong port. | Ensure `.env` has `DB_HOST=db` and `DB_PORT=5432`. Container-to-container traffic uses internal service names, not `localhost` or host-mapped port `5433`. |
| `container name "ledgerly-app" is already in use` | Stale container lock in Podman. | Run `podman rm -f ledgerly-app` or use `./scripts/restart_app.sh`. |
| Database container fails to initialize | Missing or corrupt volume data. | Reset the database state with `podman compose down -v` followed by `podman compose up -d`. |

### Useful Commands

* **Access DB via Terminal (psql)**: `podman exec -it ledgerly-db psql -U ledgerly -d ledgerly_db`
* **View App Logs**: `podman logs -f ledgerly-app`
* **View Database Logs**: `podman logs -f ledgerly-db`
* **Inspect Active Containers**: `podman ps`
* **Stop All Stack Services**: `podman compose down`