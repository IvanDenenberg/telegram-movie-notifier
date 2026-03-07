from typing import Set, Optional
import logging


class SecurityManager:
    """
    Utilidad para sanitizar datos sensibles en logs y mensajes.
    Previene exposure de API keys y tokens en output.
    """

    def __init__(self):
        self.sensitive_keys: Set[str] = set()

    def add_sensitive_key(self, key: Optional[str]):
        """Registra una API key o token como sensible"""
        if key and isinstance(key, str) and key.strip():
            self.sensitive_keys.add(key.strip())

    def sanitize(self, text: str) -> str:
        """
        Sanitiza un string, reemplazando keys sensibles con ***REDACTED***
        """
        if not text:
            return text

        sanitized = text
        for key in self.sensitive_keys:
            if key in sanitized:
                sanitized = sanitized.replace(key, "***REDACTED***")

        return sanitized

    def get_sanitized_logger(self, name: str) -> logging.Logger:
        """
        Retorna un logger que sanitiza mensajes automáticamente
        """
        logger = logging.getLogger(name)
        handler = SanitizingHandler(self)
        logger.addHandler(handler)
        return logger


class SanitizingHandler(logging.Handler):
    """Handler de logging que sanitiza records automáticamente"""

    def __init__(self, security_manager: SecurityManager):
        super().__init__()
        self.security_manager = security_manager

    def emit(self, record: logging.LogRecord):
        """Sanitiza el mensaje antes de emitir"""
        try:
            msg = record.getMessage()
            sanitized = self.security_manager.sanitize(msg)
            record.msg = sanitized
        except Exception:
            pass  # Si sanitización falla, loguear original
