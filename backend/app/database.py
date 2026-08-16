import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    """
    Production:
        DATABASE_URL=postgresql://user:password@host:5432/database

    Local development:
        falls back to POSTGRES_* variables.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()

    if database_url:
        return psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=10,
        )

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "jainai"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD") or None,
        row_factory=dict_row,
        connect_timeout=10,
    )
