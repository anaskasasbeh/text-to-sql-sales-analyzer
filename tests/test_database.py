import re
import sqlite3

import pytest

from app.database import connect_readonly
from app.prompt import COLUMN_DOCS


def test_all_rows_and_columns_are_loaded(sales_df):
    assert sales_df.shape == (2823, 25)


def test_north_america_territory_is_not_read_as_missing(db_path):
    conn = connect_readonly(db_path)
    count = conn.execute("SELECT COUNT(*) FROM sales WHERE TERRITORY = 'NA'").fetchone()[0]
    conn.close()
    assert count == 1074


def test_order_dates_are_iso_so_sqlite_date_functions_work(db_path):
    conn = connect_readonly(db_path)
    dates = [row[0] for row in conn.execute("SELECT ORDERDATE FROM sales")]
    first, last = conn.execute("SELECT MIN(ORDERDATE), MAX(ORDERDATE) FROM sales").fetchone()
    year = conn.execute("SELECT strftime('%Y', ORDERDATE) FROM sales LIMIT 1").fetchone()[0]
    conn.close()
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in dates)
    assert (first, last) == ("2003-01-06", "2005-05-31")
    assert year == "2003"


def test_table_columns_match_the_prompt_description(db_path):
    conn = connect_readonly(db_path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(sales)")]
    conn.close()
    assert columns == list(COLUMN_DOCS)


def test_readonly_connection_rejects_writes(db_path):
    conn = connect_readonly(db_path)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM sales")
    conn.close()
