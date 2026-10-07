# 📊 Ledgerly

**Ledgerly** is a privacy-first, fully containerized personal finance ETL (Extract, Transform, Load) engine and analytics workspace wrapped in a native cross-platform desktop wrapper. It processes raw financial export files, applies automated normalization and local AI-assisted categorization, stores structured data in PostgreSQL, and provides an interactive Streamlit desktop interface for exploring transactions and spending trends.

---

## 🚀 Desktop Application: How to Use

Launch Ledgerly using the desktop executable or by running `python desktop_app.py`. The native PyWebView wrapper automatically handles local service health checks, spins up the underlying container environment, manages local AI server initialization, and handles database snapshot backups upon closing.

1. 📥 **Process & Upload Tab**: Drag and drop raw bank statement CSVs. Select your bank format and click **Run ETL Pipeline**. The `ETLRunner` handles extraction, normalization, and deduplication asynchronously without locking the UI.
2. 💾 **Save Report Tab**: Export cleaned transaction datasets and generate summary financial reports for external analysis or archiving.
3. 📂 **Transactions Tab**: Query PostgreSQL live to inspect incoming records, filter by date ranges, account names, or categories, and search specific line items.
4. 📜 **Rules Tab**: Manage dynamic database classification rules to fine-tune merchant and payroll categorization patterns without editing source code.
5. 📊 **Dashboard Tab**: Explore interactive hero KPIs, monthly net cash flows, dynamic payroll/income classification, smart full-month trend filters, and category/merchant expense breakdowns.
6. 💡 **About Tab**: Inspect active environment settings, local AI model parameters, system status, and app configuration details.

---

## 🌟 Features

* **Native PyWebView Desktop Interface**: Runs inside a clean, dedicated window wrapper with an animated loading screen, automatic container lifecycle management, and clean graceful shutdowns.
* **Modular Streamlit Architecture**: Organized tab-based interface (`Process & Upload`, `Save Report`, `Transactions`, `Rules`, `Dashboard`, `About`) housed neatly in the `views/` directory.
* **Automated Database Backup on Exit**: Generates a raw `.sql` database snapshot inside the `backups/` directory before stopping containers during app exit.
* **Smart Monthly Analytics & Filtering**: Intelligent date logic automatically excludes partial historical months from trends, showing full calendar months alongside active ongoing periods for clean month-over-month comparisons.
* **Interactive Financial Dashboard**: Plotly-powered visual insights featuring Hero KPI metrics (In-Flow, Out-Flow, Net-Flow, and averages), Monthly Net Cash Flow bar charts, dynamic Income & Payroll tracking, and merchant/category expense drill-downs.
* **Dynamic Database Rules & Local AI**: Combines dynamic pattern-matching rules with a local vLLM inference server (e.g., Qwen2.5) to categorize ambiguous transactions while keeping 100% of sensitive financial data on-device.
* **Asynchronous Ingestion Pipeline**: Powered by `ETLRunner` to seamlessly process, normalize, and load bank statement CSVs into PostgreSQL.
* **Containerized Microservices**: Orchestrated with Podman / Docker Compose using isolated containers for PostgreSQL (`ledgerly-db`) and the Streamlit frontend (`ledgerly-app`).

---

## ⚙️ How to Setup & Launch

### Prerequisites

* [Podman](https://podman.io) (with `podman-compose`) or [Docker](https://www.docker.com/) (with `docker compose`)
* Python 3.12+
* WebKitGTK dependencies (Linux) or Edge WebView2 Runtime (Windows)

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

### 2. Launch Desktop Application

Run the Python desktop application entrypoint:

```bash
python desktop_app.py
```

*The launcher will automatically verify environment files, check local vLLM AI status, spin up containers via compose, launch the native PyWebView interface, and perform a database snapshot backup before stopping containers upon window exit.*

---

## 🛠️ Development & Debugging

### Running Headless / Container-Only

If developing or testing without the PyWebView window wrapper, you can spin up the container stack directly:

```bash
podman compose up -d --build
```

**!!!ONLY if you need to wipe the entire database!!!** You can clear the database container stack directly:

```bash
podman compose down -v
```

Access the Streamlit application directly in your browser at **`http://localhost:8501`**.

### Manual Database Backup

To execute a database snapshot manually outside the app shutdown sequence:

```bash
python scripts/backup_db.py
```

### Quick Application Restart

If you update environment variables or package configuration while testing containers directly, run the dedicated restart script to cleanly rebuild the app container without tearing down the database:

```bash
./scripts/restart_app.sh
```

### Common Issues & Troubleshooting

| Error / Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `Failed to load module "canberra-gtk-module"` | Missing GTK sound module on Linux. | Non-fatal warning, but can be resolved on Ubuntu via `sudo apt install libcanberra-gtk-module`. |
| `psycopg2.OperationalError: connection ... refused` | App attempting to connect to `localhost` or wrong port. | Ensure `.env` has `DB_HOST=db` and `DB_PORT=5432`. Container-to-container traffic uses internal service names. |
| `container name "ledgerly-app" is already in use` | Stale container lock in Podman. | Run `podman rm -f ledgerly-app` or use `./scripts/restart_app.sh`. |
| Database container fails to initialize | Missing or corrupt volume data. | Reset the database state with `podman compose down -v` followed by `podman compose up -d`. |

### Useful Commands

* **Access DB via Terminal (psql)**: `podman exec -it ledgerly-db psql -U ledgerly -d ledgerly_db`
* **View App Logs**: `podman logs -f ledgerly-app`
* **View Database Logs**: `podman logs -f ledgerly-db`
* **Inspect Active Containers**: `podman ps`
* **Stop All Stack Services**: `podman compose down`