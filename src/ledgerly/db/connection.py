import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_url() -> str:
    """Constructs or retrieves the database connection string."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://ledgerly:ledgerly_local_sec_pass@localhost:5433/ledgerly_db",
    )


@contextmanager
def get_db_connection():
    """Context manager providing a transactional PostgreSQL connection."""
    conn = psycopg2.connect(get_db_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_db_cursor(commit: bool = True):
    """Context manager directly providing a cursor and handling commit/rollback."""
    conn = psycopg2.connect(get_db_url())
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()