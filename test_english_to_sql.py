"""Unit tests for the English-to-SQL demo."""
import unittest

from english_to_sql import EnglishToSQLConverter


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.c = EnglishToSQLConverter()

    def test_show_all(self):
        self.assertEqual(self.c.convert("Show all employees").sql, "SELECT * FROM employees;")

    def test_count_in_department(self):
        r = self.c.convert("count employees in sales")
        self.assertEqual(r.sql, "SELECT COUNT(*) AS total_count FROM employees WHERE department = 'sales';")
        self.assertEqual(r.intent, "count")

    def test_average_with_where(self):
        self.assertEqual(
            self.c.convert("average salary where department is engineering").sql,
            "SELECT AVG(salary) AS avg_salary FROM employees WHERE department = 'engineering';",
        )

    def test_numeric_comparison(self):
        self.assertEqual(
            self.c.convert("max salary where age >= 30").sql,
            "SELECT MAX(salary) AS max_salary FROM employees WHERE age >= 30;",
        )

    def test_custom_table(self):
        self.assertEqual(self.c.convert("list all", table="loans").sql, "SELECT * FROM loans;")

    def test_unsupported(self):
        with self.assertRaises(ValueError):
            self.c.convert("tell me a joke")


if __name__ == "__main__":
    unittest.main()
