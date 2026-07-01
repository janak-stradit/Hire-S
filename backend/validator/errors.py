class ValidatorError(Exception):
    """Base exception for validator failures."""


class ValidatorInputError(ValidatorError):
    """Raised when an application cannot be evaluated from available data."""

