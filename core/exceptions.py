from enum import Enum, auto

class FailureType(Enum):
    """
    Categorizes the nature of a failure to determine the recovery strategy.
    As per rules:
    - TRANSIENT: Retry with backoff.
    - PERMISSION: Ask user for elevation.
    - AMBIGUITY: Ask user for clarification.
    - FATAL: Fail gracefully.
    """
    TRANSIENT = auto()
    PERMISSION = auto()
    AMBIGUITY = auto()
    FATAL = auto()
    INVALID_STATE = auto()
    MISSING_RESOURCE = auto()
    CONFIGURATION = auto()

class JarvisException(Exception):
    """Base exception for all Jarvis-related errors."""
    def __init__(self, message: str, failure_type: FailureType = FailureType.FATAL):
        super().__init__(message)
        self.failure_type = failure_type

class ComponentException(JarvisException):
    """Exception raised by specific components."""
    pass
