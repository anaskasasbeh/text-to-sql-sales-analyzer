"""Build the prompt that turns a question into one SQLite query.

Two prompt styles are kept so the evaluation can measure how much the schema
description helps:

- "full": column types, a short description of every column, the allowed text
  values and notes about traps in this dataset.
- "names": only the table and column names.
"""

from __future__ import annotations

from typing import Literal

PromptStyle = Literal["full", "names"]

# Column name -> (SQLite type, description). Keep in the same order as the table.
COLUMN_DOCS: dict[str, tuple[str, str]] = {
    "ORDERNUMBER": ("INTEGER", "Order ID. One order has several rows (one per product)."),
    "QUANTITYORDERED": ("INTEGER", "Units of this product in the order line."),
    "PRICEEACH": ("REAL", "Unit price, capped at 100. Do not use it to compute revenue."),
    "ORDERLINENUMBER": ("INTEGER", "Position of the line inside the order (1-18)."),
    "SALES": ("REAL", "Revenue of this order line."),
    "ORDERDATE": ("TEXT", "Order date as 'YYYY-MM-DD'."),
    "STATUS": ("TEXT", "'Shipped', 'Cancelled', 'Resolved', 'On Hold', 'In Process', 'Disputed'."),
    "QTR_ID": ("INTEGER", "Quarter of ORDERDATE (1-4)."),
    "MONTH_ID": ("INTEGER", "Month of ORDERDATE (1-12)."),
    "YEAR_ID": ("INTEGER", "Year of ORDERDATE: 2003, 2004 or 2005."),
    "PRODUCTLINE": (
        "TEXT",
        (
            "'Classic Cars', 'Vintage Cars', 'Motorcycles', 'Planes', 'Trucks and Buses', "
            "'Ships', 'Trains'."
        ),
    ),
    "MSRP": ("INTEGER", "Manufacturer's suggested retail price per unit."),
    "PRODUCTCODE": ("TEXT", "Product ID, e.g. 'S10_1678' (109 products)."),
    "CUSTOMERNAME": ("TEXT", "Customer company name (92 customers)."),
    "PHONE": ("TEXT", "Customer phone number."),
    "ADDRESSLINE1": ("TEXT", "Customer street address."),
    "ADDRESSLINE2": ("TEXT", "Extra address line, usually NULL."),
    "CITY": ("TEXT", "Customer city, e.g. 'NYC', 'Paris', 'Madrid'."),
    "STATE": ("TEXT", "State or region, e.g. 'CA', 'NY'. NULL for most non-US customers."),
    "POSTALCODE": ("TEXT", "Postal code, sometimes NULL."),
    "COUNTRY": (
        "TEXT",
        (
            "'USA', 'Spain', 'France', 'Australia', 'UK', 'Italy', 'Finland', 'Norway', "
            "'Singapore', 'Canada', 'Denmark', 'Germany', 'Sweden', 'Austria', 'Japan', "
            "'Belgium', 'Switzerland', 'Philippines', 'Ireland'."
        ),
    ),
    "TERRITORY": ("TEXT", "'NA' (North America), 'EMEA', 'APAC', 'Japan'."),
    "CONTACTLASTNAME": ("TEXT", "Last name of the customer's contact person."),
    "CONTACTFIRSTNAME": ("TEXT", "First name of the customer's contact person."),
    "DEALSIZE": ("TEXT", "'Small' (SALES < 3000), 'Medium' (3000-7000), 'Large' (> 7000)."),
}

RULES = """You write SQLite queries for a sales database with one table named `sales`.

Rules:
- Write exactly one read-only query (SELECT, or WITH ... SELECT) for SQLite.
- Use only the table and columns below.
- The question may be in English or Arabic (Modern Standard Arabic or Jordanian dialect).
  Text values in the table are in English, so translate names of countries, cities,
  product lines and statuses to the English values used in the data.
- Give result columns short English aliases in snake_case (for example total_sales),
  even when the question is in Arabic.
- For "top", "highest" or "most" questions, use ORDER BY with LIMIT.
- Do not round numbers; the app formats them.
- If the question cannot be answered from this table, reply with one line:
  CANNOT_ANSWER: <a short reason, in the language of the question>
- Otherwise reply with the SQL only, inside a ```sql code block. No explanation."""

DATA_NOTES = """Data notes:
- One row is one order line (one product inside an order). An order has several rows,
  so count orders with COUNT(DISTINCT ORDERNUMBER).
- "Sales" or "revenue" means SUM(SALES). Do not compute QUANTITYORDERED * PRICEEACH,
  because PRICEEACH is capped at 100.
- The data covers 2003-01-06 to 2005-05-31, so 2005 has January to May only.
  Use YEAR_ID, QTR_ID and MONTH_ID, or strftime() on ORDERDATE.
- The table has no costs or profit, no salespeople and no stock levels. A question that
  needs them cannot be answered: do not use SALES in their place.
- A customer is CUSTOMERNAME. Cities use local or short spellings, for example
  'NYC' (New York), 'Kobenhavn' (Copenhagen), 'Koln' (Cologne), 'Torino' (Turin),
  'Bruxelles' (Brussels), 'Gensve' (Geneva)."""

FIX_REQUEST = """That query failed in SQLite with this error:
{error}

Fix it. Reply with the corrected SQL only, inside a ```sql code block."""


def schema_block(style: PromptStyle) -> str:
    """Describe the `sales` table in the given style."""
    if style == "names":
        return f"Table:\nsales ({', '.join(COLUMN_DOCS)})"
    lines = [
        f"  {name} {sql_type},  -- {description}"
        for name, (sql_type, description) in COLUMN_DOCS.items()
    ]
    lines[-1] = lines[-1].replace(",  --", "  --", 1)
    return "Table:\nCREATE TABLE sales (\n" + "\n".join(lines) + "\n);\n\n" + DATA_NOTES


def build_prompt(question: str, style: PromptStyle = "full") -> str:
    """Return the full user message: rules, schema, then the question."""
    return f"{RULES}\n\n{schema_block(style)}\n\nQuestion: {question.strip()}"


def build_fix_request(error: str) -> str:
    """Return the follow-up message that asks the model to fix a failed query."""
    return FIX_REQUEST.format(error=error)
