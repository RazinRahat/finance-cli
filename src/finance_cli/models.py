from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    transaction_date: date
    description: str
    amount: Decimal
    category: str = "Uncategorized"
    id: int | None = None
