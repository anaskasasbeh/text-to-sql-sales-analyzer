import json

import pytest

import evaluation.run_eval as run_eval
from app.database import connect_readonly
from app.llm import LLMUnavailable
from app.sql_guard import validate_sql
from evaluation.compare import load_questions, normalize, results_match
from evaluation.report import build_report
from evaluation.run_eval import keep_matching_results, prompt_fingerprint

QUESTIONS = load_questions()


def test_question_set_shape():
    assert len(QUESTIONS) == 22
    assert len({q.id for q in QUESTIONS}) == 22
    assert sum(not q.answerable for q in QUESTIONS) == 4
    assert all(q.en and q.ar for q in QUESTIONS)


@pytest.mark.parametrize("question", [q for q in QUESTIONS if q.answerable], ids=lambda q: q.id)
def test_every_gold_query_is_safe_and_returns_rows(db_path, question):
    conn = connect_readonly(db_path)
    for sql in question.gold:
        validate_sql(sql)
        assert conn.execute(sql).fetchall(), sql
    conn.close()


def test_normalize_treats_equal_answers_as_equal():
    assert normalize(2) == normalize(2.0) == normalize("02") == normalize(" 2.001 ")
    assert normalize(2350817.7300000004) == 2350817.73
    assert normalize("USA") == "USA"
    assert normalize(None) is None


def test_extra_columns_and_column_order_are_allowed():
    gold = [["USA"]]
    assert results_match(gold, [["USA", 1685470.69]])
    assert results_match(gold, [[1685470.69, "USA"]])


def test_row_order_matters_only_for_ranked_lists():
    gold = [["a", 1], ["b", 2]]
    swapped = [["b", 2], ["a", 1]]
    assert results_match(gold, swapped, ordered=False)
    assert not results_match(gold, swapped, ordered=True)


def test_mismatches_are_detected():
    assert not results_match([[307]], [[2823]])
    assert not results_match([["a"], ["b"]], [["a"]])
    assert not results_match([["a", 1]], [["a"]])


def test_report_summarizes_runs():
    record = {
        "id": "q01",
        "lang": "en",
        "category": "aggregation",
        "answerable": True,
        "question": "What are the total sales?",
        "status": "ok",
        "correct": True,
        "first_try_correct": True,
        "sql": "SELECT SUM(SALES) FROM sales",
        "error": None,
        "calls": 1,
        "prompt_tokens": 1000,
        "completion_tokens": 100,
        "latency_ms": 900,
        "model": "openai/gpt-oss-120b",
        "prompt_style": "full",
        "run_at": "2026-11-03T10:00:00+00:00",
    }
    report = build_report({("openai/gpt-oss-120b", "full"): [record]})
    assert "| gpt-oss-120b | full | All | 100.0% (1/1) | 100.0% (1/1) |" in report
    assert "| q01 | aggregation | What are the total sales? | ✓ |  |" in report


def test_fingerprint_changes_with_the_prompt_or_settings():
    assert prompt_fingerprint("full", "low") == prompt_fingerprint("full", "low")
    assert prompt_fingerprint("full", "low") != prompt_fingerprint("names", "low")
    assert prompt_fingerprint("full", "low") != prompt_fingerprint("full", "medium")


def test_results_from_another_prompt_are_run_again(tmp_path):
    current = prompt_fingerprint("full", "low")
    lines = [
        {"id": "q01", "lang": "en", "model": "m", "prompt_hash": current},
        {"id": "q02", "lang": "en", "model": "m", "prompt_hash": "old-prompt"},
        {"id": "q03", "lang": "en", "model": "m"},  # saved before fingerprints existed
        {"id": "q04", "lang": "en", "model": "m", "prompt_hash": current, "calls": 0},  # outage
    ]
    path = tmp_path / "run.jsonl"
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")

    assert keep_matching_results(path, "m", current) == {("q01", "en")}
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_an_outage_is_not_scored_as_a_wrong_answer(monkeypatch, db_path):
    class Unreachable:
        prompt_style = "full"

        def ask(self, question):
            raise LLMUnavailable("connection reset")

    monkeypatch.setattr(run_eval.time, "sleep", lambda seconds: None)
    counter = run_eval.CountingModel(client=None)
    record = run_eval.evaluate_one(Unreachable(), counter, QUESTIONS[0], "en", db_path, "abc")
    assert record is None
