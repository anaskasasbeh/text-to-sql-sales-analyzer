"""FastAPI service: the web page, a health check and the question endpoint."""

from __future__ import annotations

import contextlib
import logging
import math
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import load_settings
from app.database import build_database, load_sales_data
from app.llm import GroqClient, LLMNotConfigured, LLMRateLimited, LLMUnavailable
from app.rate_limit import SlidingWindowLimiter
from app.sql_guard import NoSQLFound, SQLExecutionError, UnsafeSQL
from app.text_to_sql import InvalidQuestion, TextToSQL, Unanswerable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
PORTFOLIO_ORIGIN = "https://anaskasasbeh.onrender.com"  # pings /api/health to wake the server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the database once at startup and create the pipeline."""
    settings = load_settings()
    build_database(load_sales_data(settings.csv_path), settings.db_path)
    client = GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        reasoning_effort=settings.reasoning_effort,
        max_completion_tokens=settings.max_completion_tokens,
    )
    if not client.configured:
        logger.warning("GROQ_API_KEY is not set: /api/ask will return 503.")
    app.state.settings = settings
    app.state.engine = TextToSQL(
        client,
        settings.db_path,
        max_question_chars=settings.max_question_chars,
        max_rows=settings.max_rows,
        query_timeout_seconds=settings.query_timeout_seconds,
    )
    app.state.limiter = SlidingWindowLimiter(settings.rate_limit_per_minute, 60)
    yield
    with contextlib.suppress(OSError):
        settings.db_path.unlink(missing_ok=True)


app = FastAPI(title="Text-to-SQL Sales Analyzer", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[PORTFOLIO_ORIGIN], allow_methods=["GET"])


class AskRequest(BaseModel):
    question: str = Field(max_length=2000)


def _error(status: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}, **extra}
    )


def _client_ip(request: Request) -> str:
    """The visitor's IP. Render puts it first in X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/api/health")
def health() -> dict[str, str]:
    """Fast check used to wake the server. Never calls the model."""
    return {"status": "ok"}


@app.post("/api/ask")
def ask(body: AskRequest, request: Request) -> JSONResponse:
    """Turn a question into SQL, run it and return the rows."""
    wait = request.app.state.limiter.check(_client_ip(request))
    if wait:
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(math.ceil(wait))},
            content={
                "error": {"code": "rate_limited", "message": "Too many questions. Wait a moment."},
                "retry_after": math.ceil(wait),
            },
        )

    engine: TextToSQL = request.app.state.engine
    try:
        answer = engine.ask(body.question)
    except InvalidQuestion as error:
        return _error(400, "invalid_question", str(error))
    except Unanswerable as error:
        return _error(422, "unanswerable", str(error), reason=error.reason)
    except UnsafeSQL as error:
        return _error(422, "unsafe_sql", str(error))
    except (NoSQLFound, SQLExecutionError) as error:
        return _error(422, "sql_error", str(error))
    except LLMRateLimited as error:
        if error.daily:
            return _error(503, "llm_daily_limit", "Today's free model quota is used up.")
        return _error(503, "llm_busy", "The free model quota is busy.")
    except LLMNotConfigured as error:
        logger.error("Model not configured: %s", error)
        return _error(503, "not_configured", "The model is not configured.")
    except LLMUnavailable as error:
        return _error(502, "llm_unavailable", str(error))

    logger.info(
        "Answered in %d ms, %d attempt(s), %d+%d tokens",
        answer.elapsed_ms,
        len(answer.attempts),
        answer.prompt_tokens,
        answer.completion_tokens,
    )
    return JSONResponse(
        {
            "question": body.question.strip(),
            "sql": answer.sql,
            "columns": answer.columns,
            "rows": answer.rows,
            "row_count": len(answer.rows),
            "truncated": answer.truncated,
            "attempts": len(answer.attempts),
            "elapsed_ms": answer.elapsed_ms,
            "model": request.app.state.settings.groq_model,
        }
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
