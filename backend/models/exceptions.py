class InputValidationError(ValueError):
    """Raised when patient intake data is invalid."""


class AgentProcessingError(RuntimeError):
    """Raised when the multi-agent pipeline cannot complete."""

