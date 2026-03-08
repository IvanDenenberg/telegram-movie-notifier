import logging
import pytest
from backend.parser import MessageParser


class TestMessageParser:
    def setup_method(self):
        self.parser = MessageParser()

    def test_parse_add_command(self):
        result = self.parser.parse('/add "Dune"')
        assert result["type"] == "command"
        assert result["command"] == "add"
        assert result["args"] == ["Dune"]

    def test_parse_add_actor_command(self):
        result = self.parser.parse('/add_actor "Tom Cruise"')
        assert result["type"] == "command"
        assert result["command"] == "add_actor"
        assert result["args"] == ["Tom Cruise"]

    def test_parse_list_command(self):
        result = self.parser.parse('/list')
        assert result["type"] == "command"
        assert result["command"] == "list"
        assert result["args"] == []

    def test_parse_free_text(self):
        result = self.parser.parse("Quiero ver películas de Spielberg")
        assert result["type"] == "free_text"
        assert result["text"] == "Quiero ver películas de Spielberg"

    def test_parse_remove_command(self):
        result = self.parser.parse('/remove "Dune"')
        assert result["type"] == "command"
        assert result["command"] == "remove"
        assert result["args"] == ["Dune"]

    def test_parse_help_command(self):
        result = self.parser.parse('/help')
        assert result["type"] == "command"
        assert result["command"] == "help"
        assert result["args"] == []

    def test_parse_logs_command_details(self, caplog):
        parser = MessageParser()
        with caplog.at_level(logging.DEBUG):
            result = parser.parse('/add "Dune"')

        assert 'command' in caplog.text.lower()
        assert 'dune' in caplog.text.lower()
