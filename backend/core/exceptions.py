class DariException(Exception):
    """Base exception for all Dari backend errors."""
    pass

class AgentError(DariException):
    """Raised when an agent fails to execute or is not found."""
    pass

class RouteError(DariException):
    """Raised when geocoding or pathfinding fails."""
    pass

class GeocodeError(RouteError):
    """Raised when a place name cannot be resolved to coordinates."""
    pass

class LLMError(DariException):
    """Raised when the LLM service returns an error or is unreachable."""
    pass

class DocumentError(DariException):
    """Raised when the DocumentAgent fails to read, analyse, or write docs."""
    pass
