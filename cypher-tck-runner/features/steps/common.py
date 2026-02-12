
from dataclasses import dataclass
from typing import Any


@dataclass
class ResultTable: 
    columns: list[str] 
    rows: list[list[Any]]

    def is_empty(self) -> bool:
        return len(self.rows) == 0