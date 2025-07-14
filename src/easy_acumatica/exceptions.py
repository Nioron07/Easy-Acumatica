# src/easy_acumatica/exceptions.py

class AcumaticaError(Exception):
    """Base exception class for all errors related to the Acumatica API."""
    pass

class AcumaticaAuthError(AcumaticaError):
    """Raised for authentication-related errors (e.g., 401, 403)."""
    pass