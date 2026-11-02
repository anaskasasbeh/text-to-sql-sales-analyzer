import pytest

from app.prompt import build_prompt
from app.sql_guard import SQLExecutionError, UnsafeSQL
from app.text_to_sql import InvalidQuestion, TextToSQL, Unanswerable
from tests.conftest import FakeModel, sql_reply


def test_answers_a_question(db_path):
    model = FakeModel(sql_reply("SELECT ROUND(SUM(SALES), 2) AS total FROM sales WHERE QTR_ID = 1"))
    answer = TextToSQL(model, db_path).ask("Total sales in the first quarter?")
    assert answer.columns == ["total"]
    assert answer.rows == [[2350817.73]]
    assert len(answer.attempts) == 1
    assert model.calls[0][0]["content"].endswith("Question: Total sales in the first quarter?")


def test_sends_the_error_back_once_and_uses_the_fixed_query(db_path):
    model = FakeModel(
        sql_reply("SELECT SUM(SALEZ) FROM sales"),
        sql_reply("SELECT COUNT(*) FROM sales"),
    )
    answer = TextToSQL(model, db_path).ask("How many rows?")
    assert answer.rows == [[2823]]
    assert [a.error is None for a in answer.attempts] == [False, True]
    fix_request = model.calls[1][-1]["content"]
    assert "no such column: SALEZ" in fix_request


def test_gives_up_after_the_second_failure(db_path):
    model = FakeModel(sql_reply("SELECT SALEZ FROM sales"))
    with pytest.raises(SQLExecutionError):
        TextToSQL(model, db_path).ask("Broken")
    assert len(model.calls) == 2


def test_unsafe_sql_is_never_retried(db_path):
    model = FakeModel(sql_reply("DELETE FROM sales"))
    with pytest.raises(UnsafeSQL):
        TextToSQL(model, db_path).ask("Delete everything")
    assert len(model.calls) == 1


def test_unanswerable_question_keeps_the_models_reason(db_path):
    model = FakeModel("CANNOT_ANSWER: There is no weather data.")
    with pytest.raises(Unanswerable) as error:
        TextToSQL(model, db_path).ask("What's the weather in Amman?")
    assert error.value.reason == "There is no weather data."


@pytest.mark.parametrize("question", ["", "   ", "x" * 301])
def test_rejects_empty_or_too_long_questions(db_path, question):
    model = FakeModel(sql_reply("SELECT 1"))
    with pytest.raises(InvalidQuestion):
        TextToSQL(model, db_path).ask(question)
    assert model.calls == []


def test_full_prompt_describes_data_traps_and_names_prompt_does_not():
    full = build_prompt("q", "full")
    names = build_prompt("q", "names")
    assert "'NA' (North America)" in full
    assert "COUNT(DISTINCT ORDERNUMBER)" in full
    assert "PRICEEACH is capped" in full
    assert "North America" not in names
    assert "sales (ORDERNUMBER, QUANTITYORDERED" in names
