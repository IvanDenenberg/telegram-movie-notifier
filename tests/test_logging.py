import logging
from backend.handlers import CommandHandler

def test_command_handler_has_logger():
    handler = CommandHandler("test_key", "data/test.json")
    assert hasattr(handler, 'logger')
    assert isinstance(handler.logger, logging.Logger)
