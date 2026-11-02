# Text-to-SQL Sales Analyzer

Ask questions about sales data in English or Arabic. An LLM writes the SQLite query, and the app checks it and runs it read-only.

## Quick start

Requires Python 3.11+ and a free [Groq API key](https://console.groq.com/keys).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env             # then put your key in .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## License

MIT. The dataset is [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data) (CC0).
