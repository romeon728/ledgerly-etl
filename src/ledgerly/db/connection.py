from contextlib import contextmanager
import psycopg2
from psycopg2.extensions import connection as PostgresConnection
from ledgerly.config import settings


class DatabaseConnection:
    """Manages secure connections to the PostgreSQL database."""

    @staticmethod
    def get_connection() -> PostgresConnection:
        """Establishes and returns a new database connection."""
        return psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )

    @classmethod
    @contextmanager
    def session(cls):
        """Context manager for safe transaction handling and auto-closing connections."""
        conn = cls.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()