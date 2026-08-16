import os
from pathlib import Path

import psycopg


def main():
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise SystemExit("DATABASE_URL is required for production migrations")

    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"

    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        raise SystemExit("No migrations found")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for sql_file in sql_files:
                print(f"Applying {sql_file.name}")
                cur.execute(sql_file.read_text())
                conn.commit()

    print("Database migrations complete")


if __name__ == "__main__":
    main()
