# 📊 Natural Language to SQL with Pandas, SQLite, and OpenAI

This project allows users to input natural language questions and automatically generate and execute corresponding SQL queries on a pandas DataFrame using OpenAI's GPT-3.5 models.

---

## 🎓 Project Objective

To bridge the gap between non-technical users and relational data analysis by converting natural language prompts (e.g., "total sales per quarter") into SQL statements and executing them on real data.

---

## 💡 How It Works

1. **Pandas DataFrame**: Load and inspect the dataset containing sales and customer information.
2. **Temporary SQLite Database**: Convert the DataFrame into a SQL table in memory using SQLAlchemy.
3. **Prompt Engineering**:

   * Create a textual representation of the SQL table structure.
   * Combine it with the user's natural language input.
4. **OpenAI API Call**:

   * Send the combined prompt to the OpenAI Chat or Instruct model to generate a SQL query.
5. **SQL Execution**:

   * Run the generated SQL on the in-memory SQLite database.
   * Fetch and display the results.

---

## 📄 Dataset Structure

The dataset (`df`) contains the following columns:

```
['ORDERNUMBER', 'QUANTITYORDERED', 'PRICEEACH', 'ORDERLINENUMBER', 'SALES',
 'ORDERDATE', 'STATUS', 'QTR_ID', 'MONTH_ID', 'YEAR_ID', 'PRODUCTLINE', 'MSRP',
 'PRODUCTCODE', 'CUSTOMERNAME', 'PHONE', 'ADDRESSLINE1', 'ADDRESSLINE2', 'CITY',
 'STATE', 'POSTALCODE', 'COUNTRY', 'TERRITORY', 'CONTACTLASTNAME', 'CONTACTFIRSTNAME',
 'DEALSIZE']
```

---

## 🤝 Example Use Case

**User Input (Natural Language):**

```text
Sum of SALES per POSTALCODE
```

**Generated SQL Query:**

```sql
SELECT POSTALCODE, SUM(SALES)
FROM sales
GROUP BY POSTALCODE;
```

**Execution Result:**
A table showing total sales per postal code.

---

## ⚖️ Technologies Used

* **Python**
* **Pandas**
* **SQLite** (via SQLAlchemy)
* **OpenAI GPT-3.5 Turbo / GPT-3.5 Turbo-Instruct**

---

## 🔧 Key Features

* In-memory SQL database (fast & disposable)
* Interactive natural language interface
* Full SQL generation & execution pipeline
* Works with any structured dataset

---

## 📅 Setup Instructions

1. **Install dependencies**:

```bash
pip install pandas openai sqlalchemy
```

2. **Set your OpenAI API Key**:

```python
import openai
openai.api_key = "your-api-key"
```

3. **Run the Notebook**: Execute each cell step-by-step to understand and test the flow.

---

## 📉 Potential Improvements

* Add error handling for invalid SQL responses
* Add support for table joins and multiple tables
* Build a Streamlit or web-based front-end for easier use

---

## 🌐 License

MIT License. Free to use, modify, and share.
