import pytest

from app.sql_guard import (
    NoSQLFound,
    SQLExecutionError,
    UnsafeSQL,
    extract_sql,
    run_query,
    validate_sql,
)


@pytest.mark.parametrize(
    "reply",
    [
        "```sql\nSELECT 1;\n```",
        "Here you go:\n```sqlite\nSELECT 1\n```",
        "SELECT 1;",
        "```sql\nSELECT 1",  # cut off before the closing fence
    ],
)
def test_extract_sql_handles_common_reply_shapes(reply):
    assert extract_sql(reply) == "SELECT 1"


@pytest.mark.parametrize("reply", ["CANNOT_ANSWER", "```sql\nCANNOT_ANSWER\n```"])
def test_extract_sql_returns_none_when_model_cannot_answer(reply):
    assert extract_sql(reply) is None


def test_extract_sql_raises_when_reply_is_empty():
    with pytest.raises(NoSQLFound):
        extract_sql("   ")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT SUM(SALES) FROM sales",
        "WITH t AS (SELECT COUNTRY, SALES FROM sales) SELECT COUNTRY, SUM(SALES) FROM t GROUP BY 1",
        "SELECT 'a;b' AS x FROM sales",
        "SELECT replace(CITY, 'a', 'b') FROM sales",
        "(SELECT 1)",
    ],
)
def test_validate_sql_accepts_read_only_queries(sql):
    assert validate_sql(sql) == sql


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE sales",
        "SELECT 1; DROP TABLE sales",
        "WITH x AS (SELECT 1) DELETE FROM sales",
        "SELECT * FROM sales WHERE 1 = 1 /* ; */ ; UPDATE sales SET SALES = 0",
        "PRAGMA table_info(sales)",
        "ATTACH DATABASE ':memory:' AS other",
        "INSERT INTO sales (SALES) VALUES (1)",
        "REPLACE INTO sales (SALES) VALUES (1)",
    ],
)
def test_validate_sql_blocks_anything_else(sql):
    with pytest.raises(UnsafeSQL):
        validate_sql(sql)


def test_authorizer_blocks_non_read_statements_even_without_validation(db_path):
    with pytest.raises(UnsafeSQL):
        run_query(db_path, "ATTACH DATABASE ':memory:' AS other", max_rows=10, timeout_seconds=1)


def test_run_query_returns_columns_and_rows(db_path):
    result = run_query(
        db_path,
        "SELECT COUNT(DISTINCT ORDERNUMBER) AS orders FROM sales",
        max_rows=10,
        timeout_seconds=1,
    )
    assert result.columns == ["orders"]
    assert result.rows == [[307]]
    assert result.truncated is False


def test_run_query_caps_the_number_of_rows(db_path):
    result = run_query(db_path, "SELECT * FROM sales", max_rows=50, timeout_seconds=1)
    assert len(result.rows) == 50
    assert result.truncated is True


def test_run_query_stops_slow_queries(db_path):
    endless = (
        "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n) SELECT COUNT(*) FROM n"
    )
    with pytest.raises(SQLExecutionError, match="longer than"):
        run_query(db_path, endless, max_rows=10, timeout_seconds=0.3)


def test_run_query_reports_sql_errors(db_path):
    with pytest.raises(SQLExecutionError, match="no such column"):
        run_query(db_path, "SELECT SALEZ FROM sales", max_rows=10, timeout_seconds=1)
