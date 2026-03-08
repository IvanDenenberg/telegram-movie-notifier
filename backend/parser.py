import logging
import re
from typing import Dict, Any


class MessageParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    def parse(self, message: str) -> Dict[str, Any]:
        """
        Parse a message and determine if it's a command or free text.

        Returns:
            dict: {"type": "command", "command": str, "args": list} or
                  {"type": "free_text", "text": str}
        """
        message = message.strip()
        self.logger.debug(f"[PARSE] Input: {message}")

        if message.startswith('/'):
            result = self._parse_command(message)
        else:
            result = {"type": "free_text", "text": message}

        self.logger.debug(f"[PARSE] Result: type={result.get('type')}, command={result.get('command', 'N/A')}, args={result.get('args', [])}")
        return result

    def _parse_command(self, message: str) -> Dict[str, Any]:
        """
        Parse a command message.

        Expected format: /command_name "arg1" "arg2" ...
        """
        # Match command name (everything from / to first space or end of string)
        command_match = re.match(r'/(\w+)', message)
        if not command_match:
            self.logger.debug(f"[_PARSE_COMMAND] Invalid command format: {message}")
            return {"type": "free_text", "text": message}

        command = command_match.group(1)
        self.logger.debug(f"[_PARSE_COMMAND] Command detected: {command}")

        # Extract quoted arguments
        args = self._extract_args(message)
        self.logger.debug(f"[_PARSE_COMMAND] Extracted args: {args}")

        return {
            "type": "command",
            "command": command,
            "args": args
        }

    def _extract_args(self, message: str) -> list:
        """
        Extract arguments from quoted strings in the command.

        Handles: "text" and 'text'
        """
        cleaned = []

        # Try double quotes
        double_pattern = r'"([^"]*)"'
        double_matches = re.findall(double_pattern, message)
        self.logger.debug(f"[_EXTRACT_ARGS] Double quotes found: {double_matches}")
        cleaned.extend([m.strip() for m in double_matches if m.strip()])

        # Try single quotes
        single_pattern = r"'([^']*)'"
        single_matches = re.findall(single_pattern, message)
        self.logger.debug(f"[_EXTRACT_ARGS] Single quotes found: {single_matches}")
        cleaned.extend([m.strip() for m in single_matches if m.strip()])

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for item in cleaned:
            if item not in seen:
                seen.add(item)
                result.append(item)

        self.logger.debug(f"[_EXTRACT_ARGS] Final args (deduplicated): {result}")
        return result
