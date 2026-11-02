"""Turn the model's reply into one safe, read-only SQL query, and run it.

The model's output is treated like untrusted user input. Three layers protect
the data:

1. `validate_sql` checks the text: one statement, starting with SELECT or WITH,
   with no write or admin keywords.
2. An SQLite authorizer allows only reading, so anything that slips past the text
   check is still refused by the database engine.
3. The connection is opened read-only (see `database.connect_readonly`).

Each query also has a time limit and a row limit.
"""

from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from app.database import connect_readonly

CANNOT_ANSWER = "CANNOT_ANSWER"


class NoSQLFound(ValueError):
    """The reply did not contain a query."""


class UnsafeSQL(ValueError):
    """The query is not a single read-only statement."""


class SQLExecutionError(RuntimeError):
    """SQLite could not run the query (syntax error, unknown column, timeout...)."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list]
    truncated: bool


_FENCED = re.compile(r"```[a-zA-Z]*\s*(.*?)```", re.DOTALL)
_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|ANALYZE)\b"
    r"|\bREPLACE\s+INTO\b",
    re.IGNORECASE,
)
_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}


def extract_sql(reply: str) -> str | None:
    """Get the query out of the model's reply.

    Returns None when the model says the question cannot be answered.
    Raises NoSQLFound when there is no query in the reply.
    """
    text = reply.strip()
    match = _FENCED.search(text)
    if match:
        sql = match.group(1)
    else:
        # No closed code block: drop a leftover opening or closing fence, if any.
        sql = re.sub(r"^```[a-zA-Z]*", "", text).replace("```", "")
    sql = sql.strip().rstrip(";").strip()

    if CANNOT_ANSWER in text.upper() and not re.search(r"\b(SELECT|WITH)\b", sql, re.IGNORECASE):
        return None
    if not sql:
        raise NoSQLFound("The model did not return a query.")
    return sql


def validate_sql(sql: str) -> str:
    """Check that the text is one read-only statement. Returns it unchanged."""
    masked = _COMMENT.sub(" ", _STRING_LITERAL.sub("''", sql))
    if ";" in masked:
        raise UnsafeSQL("Only one statement is allowed.")
    first_word = re.match(r"[\s(]*(\w+)", masked)
    if not first_word or first_word.group(1).upper() not in {"SELECT", "WITH"}:
        raise UnsafeSQL("Only SELECT queries are allowed.")
    forbidden = _FORBIDDEN.search(masked)
    if forbidden:
        raise UnsafeSQL(f"The keyword {forbidden.group(0).upper()} is not allowed.")
    return sql


def _read_only_authorizer(action: int, *_args: object) -> int:
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY


def run_query(db_path: Path, sql: str, max_rows: int, timeout_seconds: float) -> QueryResult:
    """Run a validated query and return at most `max_rows` rows."""
    conn = connect_readonly(db_path)
    conn.set_authorizer(_read_only_authorizer)
    deadline = time.monotonic() + timeout_seconds
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
    try:
        cursor = conn.execute(sql)
        if cursor.description is None:
            raise UnsafeSQL("Only SELECT queries are allowed.")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchmany(max_rows + 1)
    except sqlite3.DatabaseError as error:
        message = str(error)
        if "not authorized" in message:
            raise UnsafeSQL("The query tried to do something other than read data.") from error
        if "interrupted" in message:
            raise SQLExecutionError(
                f"The query took longer than {timeout_seconds:g} seconds."
            ) from error
        raise SQLExecutionError(message) from error
    finally:
        conn.close()

    return QueryResult(
        columns=columns,
        rows=[list(row) for row in rows[:max_rows]],
        truncated=len(rows) > max_rows,
    )
