"""Simple English-to-SQL converter.

This module provides a lightweight rule-based converter for common
analytical questions written in English.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SQLQuery:
    """Represents a generated SQL query and metadata."""

    sql: str
    intent: str


class EnglishToSQLConverter:
    """Convert common English prompts to SQL queries.

    Supported intents:
    - show all rows
    - count rows
    - average/sum/max/min of a column
    - filtering with simple comparison operators
    """

    def __init__(self, default_table: str = "employees") -> None:
        self.default_table = default_table

    def convert(self, text: str, table: str | None = None) -> SQLQuery:
        """Convert a plain English text request into SQL.

        Args:
            text: Natural-language request.
            table: Optional table name. Falls back to `default_table`.

        Returns:
            SQLQuery object containing SQL and inferred intent.

        Raises:
            ValueError: If no supported intent is detected.
        """

        query_text = " ".join(text.strip().lower().split())
        table_name = table or self.default_table

        if self._is_show_all(query_text):
            where_clause = self._extract_where_clause(query_text)
            sql = f"SELECT * FROM {table_name}{where_clause};"
            return SQLQuery(sql=sql, intent="select_all")

        if "count" in query_text or "how many" in query_text:
            where_clause = self._extract_where_clause(query_text)
            sql = f"SELECT COUNT(*) AS total_count FROM {table_name}{where_clause};"
            return SQLQuery(sql=sql, intent="count")

        aggregate = self._extract_aggregate(query_text)
        if aggregate:
            func, column = aggregate
            where_clause = self._extract_where_clause(query_text)
            alias = f"{func.lower()}_{column}"
            sql = f"SELECT {func}({column}) AS {alias} FROM {table_name}{where_clause};"
            return SQLQuery(sql=sql, intent=f"aggregate_{func.lower()}")

        raise ValueError(
            "Unsupported request. Try prompts like: 'count employees in sales' "
            "or 'average salary where department is engineering'."
        )

    @staticmethod
    def _is_show_all(text: str) -> bool:
        return any(phrase in text for phrase in ("show all", "list all", "get all", "display all"))

    @staticmethod
    def _extract_aggregate(text: str) -> tuple[str, str] | None:
        patterns = [
            (r"average (?P<column>[a-z_][a-z0-9_]*)", "AVG"),
            (r"avg(?: of)? (?P<column>[a-z_][a-z0-9_]*)", "AVG"),
            (r"sum(?: of)? (?P<column>[a-z_][a-z0-9_]*)", "SUM"),
            (r"maximum (?P<column>[a-z_][a-z0-9_]*)", "MAX"),
            (r"max(?: of)? (?P<column>[a-z_][a-z0-9_]*)", "MAX"),
            (r"minimum (?P<column>[a-z_][a-z0-9_]*)", "MIN"),
            (r"min(?: of)? (?P<column>[a-z_][a-z0-9_]*)", "MIN"),
        ]

        for pattern, func in patterns:
            match = re.search(pattern, text)
            if match:
                return func, match.group("column")
        return None

    @staticmethod
    def _extract_where_clause(text: str) -> str:
        """Extract a simple WHERE clause from text.

        Supported forms:
          - where <column> is <value>
          - where <column> equals <value>
          - where <column> > <value>
          - in <value>   (mapped to department = '<value>')
        """

        where_match = re.search(
            r"where (?P<col>[a-z_][a-z0-9_]*)\s*(?P<op>is|equals|=|>|<|>=|<=)\s*(?P<val>[a-z0-9_\-\.]+)",
            text,
        )
        if where_match:
            col = where_match.group("col")
            op = where_match.group("op")
            val = where_match.group("val")

            sql_op = "=" if op in {"is", "equals"} else op
            sql_val = val if _looks_numeric(val) else f"'{val}'"
            return f" WHERE {col} {sql_op} {sql_val}"

        in_match = re.search(r"\bin (?P<department>[a-z_][a-z0-9_]*)", text)
        if in_match:
            dept = in_match.group("department")
            return f" WHERE department = '{dept}'"

        return ""


def _looks_numeric(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", value))


def main() -> None:
    converter = EnglishToSQLConverter(default_table="employees")

    print("English to SQL Converter")
    print("Type 'exit' to quit.\n")

    while True:
        text = input("English query: ").strip()
        if text.lower() in {"exit", "quit"}:
            break

        try:
            result = converter.convert(text)
            print(f"SQL: {result.sql}\n")
        except ValueError as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()
