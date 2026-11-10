"""mathgen — генератор и проверка школьных задач по математике (точная арифметика, без зависимостей)."""
from .check import Result, check
from .problem import Problem
from .topics import LEVELS, TOPICS, from_id, generate
from .worksheet import Worksheet, build_worksheet, to_json, to_markdown

__all__ = ["Problem", "Result", "Worksheet", "TOPICS", "LEVELS", "generate", "from_id", "check",
           "build_worksheet", "to_markdown", "to_json"]
__version__ = "0.1.0"
