class FinanceCLIError(Exception):
    """Base class for expected finance CLI errors."""


class InvalidTransactionError(FinanceCLIError):
    """Raised when transaction data cannot be parsed."""


class InvalidStatementError(FinanceCLIError):
    """Raised when a bank statement has an invalid structure."""


class StatementNotFoundError(FinanceCLIError):
    """Raised when a requested bank statement cannot be found."""
