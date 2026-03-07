import unittest
from backend.security import SecurityManager


class TestSecurityManager(unittest.TestCase):
    def test_sanitize_sensitive_data(self):
        """Test sanitiza API keys de strings"""
        manager = SecurityManager()
        manager.add_sensitive_key("test_key_123")

        text = "Usando API key: test_key_123 en request"
        sanitized = manager.sanitize(text)

        assert "test_key_123" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_multiple_keys_sanitized(self):
        """Test sanitiza múltiples keys"""
        manager = SecurityManager()
        manager.add_sensitive_key("key1")
        manager.add_sensitive_key("key2")

        text = "key1 and key2 in one string"
        sanitized = manager.sanitize(text)

        assert "key1" not in sanitized
        assert "key2" not in sanitized

    def test_sanitize_empty_string(self):
        """Test maneja strings vacíos"""
        manager = SecurityManager()
        manager.add_sensitive_key("key")

        result = manager.sanitize("")
        assert result == ""

    def test_sanitize_none_key(self):
        """Test ignora keys None"""
        manager = SecurityManager()
        manager.add_sensitive_key(None)

        text = "Some text"
        sanitized = manager.sanitize(text)
        assert sanitized == "Some text"
