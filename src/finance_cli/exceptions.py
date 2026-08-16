class FinanceCLIError(Exception):
    """Base class for expected finance CLI errors."""


class InvalidTransactionError(FinanceCLIError):
    """Raised when transaction data cannot be parsed."""
