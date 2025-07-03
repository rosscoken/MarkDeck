"""
MarkDeck Custom Exceptions

Custom exception classes for MarkDeck error handling.
"""


class MarkDeckError(Exception):
    """Base exception for all MarkDeck errors."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ParseError(MarkDeckError):
    """Raised when markdown parsing fails."""
    pass


class ThemeError(MarkDeckError):
    """Raised when theme processing fails."""
    pass


class GenerationError(MarkDeckError):
    """Raised when slide generation fails."""
    pass


class ExportError(MarkDeckError):
    """Raised when export process fails."""
    pass


class PluginError(MarkDeckError):
    """Raised when plugin operations fail."""
    pass


class ConfigurationError(MarkDeckError):
    """Raised when configuration is invalid."""
    pass


class ValidationError(MarkDeckError):
    """Raised when input validation fails."""
    pass


class FileNotFoundError(MarkDeckError):
    """Raised when required files are not found."""
    pass


class SchemaValidationError(MarkDeckError):
    """Raised when JSON schema validation fails."""
    
    def __init__(self, message: str, schema_errors: list = None):
        super().__init__(message)
        self.schema_errors = schema_errors or []
    
    def __str__(self) -> str:
        base_message = super().__str__()
        if self.schema_errors:
            error_details = "\n".join(f"  - {error}" for error in self.schema_errors)
            return f"{base_message}\nValidation errors:\n{error_details}"
        return base_message


class ProcessingError(MarkDeckError):
    """Raised when processing pipeline fails."""
    pass