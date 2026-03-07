import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from backend.ai_processor import AIProcessor


class TestAIProcessor(unittest.TestCase):
    def test_ai_processor_disabled_by_default(self):
        """Test AIProcessor está deshabilitado por default"""
        processor = AIProcessor(enabled=False)
        result = processor.process("test message")
        assert result is None

    def test_ai_processor_requires_api_key(self):
        """Test que habilitar IA requiere API key"""
        with patch.dict(os.environ, {}, clear=True):
            processor = AIProcessor(enabled=True)
            # Debería estar deshabilitado si falta API key
            assert processor.enabled is False

    def test_ai_processor_with_api_key(self):
        """Test AIProcessor se inicializa con API key"""
        # Mockear el módulo anthropic en sys.modules
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic = MagicMock()

        with patch.dict(sys.modules, {'anthropic': mock_anthropic}):
            with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test_key'}):
                processor = AIProcessor(enabled=True)
                assert processor.enabled is True

    @patch.dict(os.environ, {'CLAUDE_API_KEY': 'test_key'})
    def test_ai_processor_sanitizes_output(self):
        """Test que output se sanitiza"""
        processor = AIProcessor(enabled=True)
        processor.security_manager.add_sensitive_key("secret_key_123")

        response = "Comando: /add_actor secret_key_123"
        result = processor._sanitize_response(response)

        assert "secret_key_123" not in result
        assert "***REDACTED***" in result
