class FinanceCLIError(Exception):
    """Base class for expected finance CLI errors."""


class InvalidTransactionError(FinanceCLIError):
    """Raised when transaction data cannot be parsed."""


class InvalidStatementError(FinanceCLIError):
    """Raised when a bank statement has an invalid structure."""


class StatementNotFoundError(FinanceCLIError):
    """Raised when a requested bank statement cannot be found."""


class DatabaseError(FinanceCLIError):
    """Raised when transaction persistence fails."""


class DuplicateStatementError(FinanceCLIError):
    """Raised when a statement has already been imported."""


class InvalidRulesError(FinanceCLIError):
    """Raised when a category rules file is invalid."""


class InvalidCategoryError(FinanceCLIError):
    """Raised when a category name is invalid."""


class TransactionNotFoundError(FinanceCLIError):
    """Raised when a transaction ID does not exist."""
