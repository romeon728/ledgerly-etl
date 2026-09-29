import os
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load project root .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

BACKUP_DIR = PROJECT_ROOT / "backups"
RETENTION_DAYS = 30

DB_NAME = os.getenv("DB_NAME", "ledgerly_db")
DB_USER = os.getenv("DB_USER", "ledgerly")


def get_db_container_name() -> str | None:
    """Check .env for container name or auto-detect from running Podman containers."""
    env_name = os.getenv("DB_CONTAINER_NAME")
    if env_name:
        return env_name

    try:
        # Auto-detect running container using postgres image
        result = subprocess.run(
            ["podman", "ps", "--filter", "ancestor=postgres", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        containers = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
        if containers:
            return containers[0]
    except Exception:
        pass

    return None


def create_backup():
    """Execute pg_dump inside the DB container and stream to local host file."""
    container_name = get_db_container_name()
    if not container_name:
        print("❌ Error: Could not detect running database container. Set DB_CONTAINER_NAME in .env.")
        return

    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"ledgerly_backup_{timestamp}.sql"

    cmd = [
        "podman",
        "exec",
        "-t",
        container_name,
        "pg_dump",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
    ]

    try:
        print(f"Creating backup at '{backup_file.name}' via container '{container_name}'...")
        with open(backup_file, "w", encoding="utf-8") as f:
            subprocess.run(cmd, stdout=f, check=True)
        print("✅ Backup completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed with exit code {e.returncode}")
        if backup_file.exists():
            backup_file.unlink()
        return
    except FileNotFoundError:
        print("❌ Error: 'podman' command not found in host PATH.")
        return

    cutoff_time = datetime.now().timestamp() - (RETENTION_DAYS * 86400)
    for old_file in BACKUP_DIR.glob("ledgerly_backup_*.sql"):
        if old_file.stat().st_mtime < cutoff_time:
            old_file.unlink()
            print(f"🗑️ Removed expired backup: {old_file.name}")


if __name__ == "__main__":
    create_backup()