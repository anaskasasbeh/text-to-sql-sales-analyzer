import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from app.llm import GroqClient, LLMRateLimited, _rate_limit_error
from app.main import app
from app.rate_limit import SlidingWindowLimiter
from app.text_to_sql import TextToSQL
from tests.conftest import FakeModel, sql_reply


@pytest.fixture
def client(db_path):
    with TestClient(app) as test_client:
        app.state.limiter = SlidingWindowLimiter(15, 60)
        yield test_client


def use_model(model, db_path):
    app.state.engine = TextToSQL(model, db_path)


def test_health_is_fast_and_never_calls_the_model(client, db_path):
    model = FakeModel(sql_reply("SELECT 1"))
    use_model(model, db_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert model.calls == []


def test_home_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Text-to-SQL Sales Analyzer" in response.text


def test_ask_returns_sql_and_rows(client, db_path):
    sql = "SELECT COUNT(DISTINCT ORDERNUMBER) AS orders FROM sales WHERE STATUS = 'Cancelled'"
    use_model(FakeModel(sql_reply(sql)), db_path)
    response = client.post("/api/ask", json={"question": "How many orders were cancelled?"})
    body = response.json()
    assert response.status_code == 200
    assert body["sql"] == sql
    assert body["columns"] == ["orders"]
    assert body["rows"] == [[4]]
    assert body["attempts"] == 1


@pytest.mark.parametrize(
    ("reply", "status", "code"),
    [
        ("CANNOT_ANSWER", 422, "unanswerable"),
        (sql_reply("DROP TABLE sales"), 422, "unsafe_sql"),
        (sql_reply("SELECT nope FROM sales"), 422, "sql_error"),
        (LLMRateLimited("tpm", retry_after=5, daily=False), 503, "llm_busy"),
        (LLMRateLimited("tpd", retry_after=None, daily=True), 503, "llm_daily_limit"),
    ],
)
def test_errors_have_stable_codes(client, db_path, reply, status, code):
    use_model(FakeModel(reply), db_path)
    response = client.post("/api/ask", json={"question": "anything"})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_missing_api_key_returns_503(client, db_path):
    use_model(GroqClient(api_key="", model="openai/gpt-oss-120b"), db_path)
    response = client.post("/api/ask", json={"question": "Total sales?"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "not_configured"


def test_each_ip_gets_15_questions_per_minute(client, db_path):
    use_model(FakeModel(sql_reply("SELECT 1 AS one")), db_path)
    headers = {"X-Forwarded-For": "203.0.113.7"}
    for _ in range(15):
        assert client.post("/api/ask", json={"question": "q"}, headers=headers).status_code == 200
    blocked = client.post("/api/ask", json={"question": "q"}, headers=headers)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    other_ip = client.post(
        "/api/ask", json={"question": "q"}, headers={"X-Forwarded-For": "198.51.100.2"}
    )
    assert other_ip.status_code == 200


def test_groq_daily_and_minute_limits_are_told_apart():
    def error(message: str) -> openai.RateLimitError:
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        response = httpx.Response(429, headers={"retry-after": "7"}, request=request)
        return openai.RateLimitError(message, response=response, body=None)

    minute = _rate_limit_error(error("Rate limit reached on tokens per minute (TPM)"))
    day = _rate_limit_error(error("Rate limit reached on tokens per day (TPD)"))
    assert (minute.daily, minute.retry_after) == (False, 7.0)
    assert day.daily is True


def test_portfolio_can_read_the_health_check(client):
    response = client.get("/api/health", headers={"Origin": "https://anaskasasbeh.onrender.com"})
    assert response.headers["access-control-allow-origin"] == "https://anaskasasbeh.onrender.com"
