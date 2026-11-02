"""Shared test helpers. No test needs the network or an API key."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import PROJECT_ROOT
from app.database import build_database, load_sales_data
from app.llm import LLMReply

CSV_PATH = PROJECT_ROOT / "data" / "sales_data_sample.csv"


class FakeModel:
    """Returns prepared replies in order and records every conversation it receives."""

    def __init__(self, *replies: str | Exception) -> None:
        self.replies = list(replies)
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> LLMReply:
        self.calls.append([dict(m) for m in messages])
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return LLMReply(text=reply, prompt_tokens=1000, completion_tokens=50, finish_reason="stop")


def sql_reply(sql: str) -> str:
    return f"```sql\n{sql}\n```"


@pytest.fixture(scope="session")
def sales_df():
    return load_sales_data(CSV_PATH)


@pytest.fixture(scope="session")
def db_path(sales_df, tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("db") / "sales.db"
    build_database(sales_df, path)
    return path
