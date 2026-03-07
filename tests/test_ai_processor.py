import unittest
from backend.ai_processor import AIProcessor


class TestAIProcessor(unittest.TestCase):
    def test_ai_processor_disabled(self):
        """Test AI processor when disabled"""
        processor = AIProcessor(enabled=False)

        result = processor.process("Add The Matrix")

        self.assertIsNone(result)

    def test_ai_processor_enabled_placeholder(self):
        """Test AI processor when enabled (placeholder)"""
        processor = AIProcessor(enabled=True)

        result = processor.process("Add The Matrix")

        self.assertIsNone(result)

    def test_ai_processor_default_disabled(self):
        """Test AI processor default state is disabled"""
        processor = AIProcessor()

        self.assertFalse(processor.enabled)
        result = processor.process("Any message")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
