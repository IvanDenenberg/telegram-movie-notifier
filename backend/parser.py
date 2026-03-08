import re
from typing import Dict, Any


class MessageParser:
    def parse(self, message: str) -> Dict[str, Any]:
        """
        Parse a message and determine if it's a command or free text.

        Returns:
            dict: {"type": "command", "command": str, "args": list} or
                  {"type": "free_text", "text": str}
        """
        message = message.strip()

        if message.startswith('/'):
            return self._parse_command(message)
        else:
            return {"type": "free_text", "text": message}

    def _parse_command(self, message: str) -> Dict[str, Any]:
        """
        Parse a command message.

        Expected format: /command_name "arg1" "arg2" ...
        """
        # Match command name (everything from / to first space or end of string)
        command_match = re.match(r'/(\w+)', message)
        if not command_match:
            return {"type": "free_text", "text": message}

        command = command_match.group(1)

        # Extract quoted arguments
        args = self._extract_args(message)

        return {
            "type": "command",
            "command": command,
            "args": args
        }

    def _extract_args(self, message: str) -> list:
        """
        Extract arguments from quoted strings in the command.

        Finds all quoted strings (handles double quotes, single quotes, and curly quotes)
        and returns them as a list, properly cleaned.
        """
        # Match quoted strings: regular quotes and curly quotes (Unicode)
        # Handles: "text", 'text', "text", 'text', etc.
        pattern = r'["\'""]([^"\'"]*)["\'""]'
        matches = re.findall(pattern, message)

        # Clean up: strip whitespace and extra quotes from each match
        cleaned = []
        for match in matches:
            # Remove any leading/trailing quotes and whitespace
            clean_str = match.strip().strip('"\' \'"').strip()
            if clean_str:  # Only add non-empty strings
                cleaned.append(clean_str)

        return cleaned
