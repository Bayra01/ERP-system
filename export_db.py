"""PostgreSQL-iin ugugdliig db_export/ havtas ruu file bolgon gargana: python export_db.py

  db_export/erp_dump.sql   - buten nuots (pg_dump). Sergeeh: psql -U erp -d <db> -f erp_dump.sql
  db_export/csv/<table>.csv - table burt neg file, Excel-eer shuud neegdene (UTF-8 BOM)

Anhaar: auth_users.password_hash zereg nuuts medeelel orno - git-d hiihgui (.gitignore).
"""
import csv
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import get_settings  # noqa: E402

OUT = ROOT / "db_export"
PG_BIN = [Path(r"C:\Program Files\PostgreSQL") / v / "bin" for v in ("18", "17", "16")]


def find_pg_dump() -> str | None:
    if found := shutil.which("pg_dump"):
        return found
    for d in PG_BIN:
        if (d / "pg_dump.exe").exists():
            return str(d / "pg_dump.exe")
    return None


def dump_sql(url) -> Path | None:
    exe = find_pg_dump()
    if exe is None:
        print("! pg_dump oldsongui - .sql dump algasav (CSV gargana)")
        return None
    target = OUT / "erp_dump.sql"
    env = {**os.environ, "PGPASSWORD": url.password or ""}
    subprocess.run([exe, "-h", url.host or "localhost", "-p", str(url.port or 5432),
                    "-U", url.username, "-d", url.database, "--no-owner", "--no-privileges",
                    "-f", str(target)], env=env, check=True)
    return target


def dump_csv(engine) -> list[tuple[str, int]]:
    folder = OUT / "csv"
    folder.mkdir(parents=True, exist_ok=True)
    result = []
    with engine.connect() as conn:
        for table in sorted(inspect(conn).get_table_names()):
            rows = conn.execute(text(f'SELECT * FROM "{table}" ORDER BY 1'))
            with open(folder / f"{table}.csv", "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(rows.keys())
                n = 0
                for r in rows:
                    w.writerow(r)
                    n += 1
            result.append((table, n))
    return result


def main() -> None:
    url = make_url(get_settings().DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        sys.exit(f"DATABASE_URL PostgreSQL bish ({url.get_backend_name()}) - .env-ee shalgana uu")
    OUT.mkdir(exist_ok=True)
    sql = dump_sql(url)
    tables = dump_csv(create_engine(url))
    width = max(len(t) for t, _ in tables)
    lines = [f"{t:<{width}}  {n:>6}" for t, n in tables]
    (OUT / "README.txt").write_text(
        f"Export: {datetime.now():%Y-%m-%d %H:%M}  DB: {url.database}@{url.host}\n\n"
        + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n-> {OUT}" + (f"\n-> {sql.name}" if sql else ""))


if __name__ == "__main__":
    main()
