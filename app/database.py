"""Load and clean the sales CSV, and serve it as a read-only SQLite database."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TABLE_NAME = "sales"


def load_sales_data(csv_path: Path) -> pd.DataFrame:
    """Read the CSV and fix the two problems that would give wrong SQL answers.

    1. TERRITORY uses "NA" for North America. pandas reads "NA" as a missing value
       by default, so only empty cells are treated as missing here.
    2. ORDERDATE looks like "2/24/2003 0:00". SQLite date functions only understand
       ISO dates, so it is stored as "2003-02-24".
    """
    df = pd.read_csv(
        csv_path,
        keep_default_na=False,
        na_values=[""],
        dtype={"PHONE": str, "POSTALCODE": str},
    )
    order_dates = pd.to_datetime(df["ORDERDATE"], format="%m/%d/%Y %H:%M")
    df["ORDERDATE"] = order_dates.dt.strftime("%Y-%m-%d")
    logger.info("Loaded %d rows and %d columns from %s", len(df), df.shape[1], csv_path.name)
    return df


def build_database(df: pd.DataFrame, db_path: Path) -> None:
    """Write the DataFrame into a fresh SQLite file as the table `sales`."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(TABLE_NAME, conn, index=False)
    conn.close()
    logger.info("Built SQLite database at %s", db_path)


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open the database in read-only mode, so no query can change the data."""
    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.execute("PRAGMA query_only = ON")
    return conn
