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

        Handles: "text", 'text', "text" (curly), 'text' (curly), and variants.
        """
        cleaned = []

        # Try double quotes first
        double_pattern = r'"([^"]*)"'
        double_matches = re.findall(double_pattern, message)
        cleaned.extend([m.strip() for m in double_matches if m.strip()])

        # Try single quotes (but avoid already matched double quotes)
        single_pattern = r"'([^']*)'"
        single_matches = re.findall(single_pattern, message)
        cleaned.extend([m.strip() for m in single_matches if m.strip()])

        # Try curly quotes (Unicode)
        curly_double = r'"([^"]*)"'
        curly_matches = re.findall(curly_double, message)
        cleaned.extend([m.strip() for m in curly_matches if m.strip()])

        # Try curly single quotes (Unicode)
        curly_single = r''([^']*)'''
        curly_single_matches = re.findall(curly_single, message)
        cleaned.extend([m.strip() for m in curly_single_matches if m.strip()])

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for item in cleaned:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result
