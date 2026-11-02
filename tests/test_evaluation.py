import pytest

from app.database import connect_readonly
from app.sql_guard import validate_sql
from evaluation.compare import load_questions, normalize, results_match
from evaluation.report import build_report

QUESTIONS = load_questions()


def test_question_set_shape():
    assert len(QUESTIONS) == 20
    assert len({q.id for q in QUESTIONS}) == 20
    assert sum(not q.answerable for q in QUESTIONS) == 2
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
