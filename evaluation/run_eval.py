"""Run the question set against Groq models and save one result line per question.

Usage (from the project root, with GROQ_API_KEY in .env):

    python -m evaluation.run_eval                 # the three default configurations
    python -m evaluation.run_eval --model openai/gpt-oss-20b --prompt full

The run is throttled to stay inside Groq's free-tier limits. If it stops (daily limit,
network), run the same command again: finished questions are kept and skipped.

Every result stores a fingerprint of the exact prompt and model settings. Results saved
with a different fingerprint (for example after a prompt change) are run again.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from app.config import PROJECT_ROOT, load_settings
from app.database import build_database, connect_readonly, load_sales_data
from app.llm import GroqClient, LLMNotConfigured, LLMRateLimited, LLMReply, LLMUnavailable
from app.prompt import PromptStyle, build_prompt
from app.sql_guard import NoSQLFound, SQLExecutionError, UnsafeSQL
from app.text_to_sql import TextToSQL, Unanswerable
from evaluation.compare import Question, load_questions, results_match
from evaluation.report import write_report

RUNS_DIR = PROJECT_ROOT / "reports" / "runs"
DEFAULT_CONFIGS: list[tuple[str, PromptStyle]] = [
    ("openai/gpt-oss-120b", "full"),
    ("openai/gpt-oss-20b", "full"),
    ("openai/gpt-oss-120b", "names"),
]
LANGUAGES = ("en", "ar")


class DailyLimitReached(RuntimeError):
    pass


class CountingModel:
    """Wraps the client to count calls and tokens for one question."""

    def __init__(self, client: GroqClient) -> None:
        self.client = client
        self.reset()

    def reset(self) -> None:
        self.calls = self.prompt_tokens = self.completion_tokens = 0

    def complete(self, messages: list[dict[str, str]]) -> LLMReply:
        reply = self.client.complete(messages)
        self.calls += 1
        self.prompt_tokens += reply.prompt_tokens
        self.completion_tokens += reply.completion_tokens
        return reply


def run_file(model: str, style: str) -> Path:
    return RUNS_DIR / f"{model.split('/')[-1]}__{style}.jsonl"


def prompt_fingerprint(style: PromptStyle, reasoning_effort: str) -> str:
    """Short hash of the prompt template and model settings used for a run."""
    text = f"{build_prompt('<question>', style)}|reasoning_effort={reasoning_effort}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def keep_matching_results(path: Path, model: str, fingerprint: str) -> set[tuple[str, str]]:
    """Drop saved results from another prompt or model; return the (id, lang) pairs kept."""
    if not path.exists():
        return set()
    kept, done = [], set()
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        record = json.loads(line)
        if record.get("prompt_hash") == fingerprint and record.get("model") == model:
            kept.append(line)
            done.add((record["id"], record["lang"]))
    if len(kept) < len(lines):
        print(
            f"  {len(lines) - len(kept)} saved results used a different prompt: running them again"
        )
        path.write_text("".join(f"{line}\n" for line in kept), encoding="utf-8")
    return done


def gold_rows(db_path: Path, question: Question) -> list[list[list]]:
    conn = connect_readonly(db_path)
    try:
        return [[list(row) for row in conn.execute(sql)] for sql in question.gold]
    finally:
        conn.close()


def evaluate_one(
    engine: TextToSQL,
    counter: CountingModel,
    question: Question,
    lang: str,
    db_path: Path,
    fingerprint: str,
) -> dict:
    """Ask one question, waiting out per-minute rate limits, and score the answer."""
    status, sql, error, rows = "error", None, None, None
    for _ in range(6):
        counter.reset()
        started = time.perf_counter()
        try:
            answer = engine.ask(question.text(lang))
            status, sql, rows = "ok", answer.sql, answer.rows
        except Unanswerable:
            status = "cannot_answer"
        except (UnsafeSQL, SQLExecutionError, NoSQLFound) as exc:
            error = str(exc)
        except LLMRateLimited as exc:
            if exc.daily:
                raise DailyLimitReached(str(exc)) from exc
            wait = (exc.retry_after or 15) + 1
            print(f"    rate limited, waiting {wait:.0f} s", flush=True)
            time.sleep(wait)
            continue
        except LLMUnavailable as exc:
            print(f"    model unavailable ({exc}), waiting 20 s", flush=True)
            time.sleep(20)
            continue
        break
    latency_ms = round((time.perf_counter() - started) * 1000)

    if question.answerable:
        correct = status == "ok" and any(
            results_match(gold, rows, question.ordered) for gold in gold_rows(db_path, question)
        )
    else:
        correct = status == "cannot_answer"

    return {
        "id": question.id,
        "lang": lang,
        "category": question.category,
        "answerable": question.answerable,
        "question": question.text(lang),
        "status": status,
        "correct": correct,
        "first_try_correct": correct and counter.calls == 1,
        "sql": sql,
        "error": error,
        "calls": counter.calls,
        "prompt_tokens": counter.prompt_tokens,
        "completion_tokens": counter.completion_tokens,
        "latency_ms": latency_ms,
        "model": engine.model.client.model,
        "prompt_style": engine.prompt_style,
        "prompt_hash": fingerprint,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def run_config(
    model: str, style: PromptStyle, questions: list[Question], db_path: Path, tpm_budget: int
) -> None:
    settings = load_settings()
    client = GroqClient(
        api_key=settings.groq_api_key,
        model=model,
        reasoning_effort=settings.reasoning_effort,
        max_completion_tokens=settings.max_completion_tokens,
    )
    counter = CountingModel(client)
    engine = TextToSQL(counter, db_path, prompt_style=style, max_rows=5000)

    path = run_file(model, style)
    path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = prompt_fingerprint(style, settings.reasoning_effort)
    print(f"\n{model} | prompt: {style} | fingerprint {fingerprint}")
    done = keep_matching_results(path, model, fingerprint)

    todo = [(q, lang) for q in questions for lang in LANGUAGES if (q.id, lang) not in done]
    print(f"  {len(todo)} to run, {len(done)} already done")
    for index, (question, lang) in enumerate(todo, start=1):
        started = time.perf_counter()
        record = evaluate_one(engine, counter, question, lang, db_path, fingerprint)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        mark = "correct" if record["correct"] else f"WRONG ({record['status']})"
        tokens = record["prompt_tokens"] + record["completion_tokens"]
        print(
            f"  [{index:>2}/{len(todo)}] {question.id} {lang}: {mark}, "
            f"{record['latency_ms']} ms, {tokens} tokens",
            flush=True,
        )
        # Stay under the tokens-per-minute limit, and under 30 requests per minute.
        min_seconds = max(tokens / tpm_budget * 60, 2.1)
        time.sleep(max(0.0, min_seconds - (time.perf_counter() - started)))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", help="Groq model ID, e.g. openai/gpt-oss-120b")
    parser.add_argument("--prompt", choices=["full", "names"], default="full")
    parser.add_argument("--tpm", type=int, default=6000, help="Tokens per minute to stay under")
    args = parser.parse_args()

    settings = load_settings()
    if not settings.groq_api_key:
        print("Set GROQ_API_KEY in .env first (see .env.example).")
        return 1

    build_database(load_sales_data(settings.csv_path), settings.db_path)
    questions = load_questions()
    configs = [(args.model, args.prompt)] if args.model else DEFAULT_CONFIGS
    try:
        for model, style in configs:
            run_config(model, style, questions, settings.db_path, args.tpm)
    except DailyLimitReached:
        print("\nGroq's daily free limit is reached. Run the same command again tomorrow;")
        print("finished questions are saved and will be skipped.")
        return 2
    except LLMNotConfigured as error:
        print(f"\n{error} Check GROQ_API_KEY in .env.")
        return 1
    finally:
        settings.db_path.unlink(missing_ok=True)
        report_path = write_report()
        print(f"\nReport written to {report_path.relative_to(PROJECT_ROOT)}")
    print("\n" + report_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
