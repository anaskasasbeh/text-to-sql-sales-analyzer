"""The full pipeline: question -> prompt -> model -> SQL -> checks -> result."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.llm import LLMReply
from app.prompt import PromptStyle, build_fix_request, build_prompt
from app.sql_guard import (
    NoSQLFound,
    SQLExecutionError,
    extract_sql,
    run_query,
    validate_sql,
)

logger = logging.getLogger(__name__)


class InvalidQuestion(ValueError):
    """The question is empty or too long."""


class Unanswerable(ValueError):
    """The model said the question cannot be answered from this table."""


class ChatModel(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> LLMReply: ...


@dataclass
class Attempt:
    sql: str | None
    error: str | None


@dataclass
class Answer:
    sql: str
    columns: list[str]
    rows: list[list]
    truncated: bool
    attempts: list[Attempt] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    elapsed_ms: int = 0


class TextToSQL:
    """Answer a question about the `sales` table with one generated SQL query."""

    def __init__(
        self,
        model: ChatModel,
        db_path: Path,
        *,
        prompt_style: PromptStyle = "full",
        max_question_chars: int = 300,
        max_rows: int = 200,
        query_timeout_seconds: float = 3.0,
        max_attempts: int = 2,
    ) -> None:
        self.model = model
        self.db_path = db_path
        self.prompt_style = prompt_style
        self.max_question_chars = max_question_chars
        self.max_rows = max_rows
        self.query_timeout_seconds = query_timeout_seconds
        self.max_attempts = max_attempts

    def ask(self, question: str) -> Answer:
        """Generate SQL for the question and run it.

        If SQLite rejects the query, the error is sent back to the model once so it
        can fix it (self-correction). Unsafe queries are never retried.
        """
        question = question.strip()
        if not question:
            raise InvalidQuestion("Please type a question.")
        if len(question) > self.max_question_chars:
            raise InvalidQuestion(
                f"Please keep the question under {self.max_question_chars} characters."
            )

        started = time.perf_counter()
        messages = [{"role": "user", "content": build_prompt(question, self.prompt_style)}]
        attempts: list[Attempt] = []
        prompt_tokens = completion_tokens = 0

        while True:
            reply = self.model.complete(messages)
            prompt_tokens += reply.prompt_tokens
            completion_tokens += reply.completion_tokens
            sql: str | None = None
            try:
                sql = extract_sql(reply.text)
                if sql is None:
                    raise Unanswerable("This question can't be answered from the sales table.")
                validate_sql(sql)  # UnsafeSQL is raised to the caller, never retried.
                result = run_query(self.db_path, sql, self.max_rows, self.query_timeout_seconds)
            except (NoSQLFound, SQLExecutionError) as error:
                attempts.append(Attempt(sql=sql, error=str(error)))
                logger.info("Attempt %d failed: %s", len(attempts), error)
                if len(attempts) >= self.max_attempts:
                    raise
                messages += [
                    {"role": "assistant", "content": reply.text},
                    {"role": "user", "content": build_fix_request(str(error))},
                ]
                continue

            attempts.append(Attempt(sql=sql, error=None))
            return Answer(
                sql=sql,
                columns=result.columns,
                rows=result.rows,
                truncated=result.truncated,
                attempts=attempts,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                elapsed_ms=round((time.perf_counter() - started) * 1000),
            )
