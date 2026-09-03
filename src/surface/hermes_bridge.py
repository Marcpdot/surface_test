# Qt-free by design.
from __future__ import annotations

import json

from surface.protocol import Command, ProtocolError, parse_command, parse_command_list


class HermesBridge:
    def from_hermes_output(self, output: str) -> list[Command]:
        """Translate an external Hermes string into commands.

        Strip, then parse_command_list.
        Stripped text that does not start with '{' or '[' → ProtocolError(cannot_translate).
        Invalid JSON / schema → ProtocolError from the parser (invalid_json, ...).
        """
        stripped = output.strip()
        if not stripped.startswith("{") and not stripped.startswith("["):
            raise ProtocolError("cannot_translate", "cannot translate Hermes output")
        return parse_command_list(stripped)

    def from_user_input(self, text: str, *, text_id: str) -> list[Command]:
        """User input bar.

        Stripped text starting with '{' or '[' → from_hermes_output
        (text_id is ignored; commands carry their own ids).
        Otherwise → parse_command as a text command (same limits as protocol).
        """
        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return self.from_hermes_output(stripped)
        return [
            parse_command(
                {
                    "type": "text",
                    "id": text_id,
                    "content": stripped,
                    "format": "markdown",
                }
            )
        ]

    @staticmethod
    def demo_output(*, image_source: str) -> str:
        """json.dumps of [text, equation, image, plot]. image_source is an
        already existing file path; json.dumps escapes backslash on Windows.
        """
        payload = [
            {
                "type": "text",
                "id": "demo-text",
                "content": "## Surface demo",
                "format": "markdown",
            },
            {"type": "equation", "id": "demo-eq", "latex": r"\sigma = \frac{My}{I}"},
            {"type": "image", "id": "demo-img", "source": image_source, "alt": "demo"},
            {
                "type": "plot",
                "id": "demo-plot",
                "title": "demo",
                "series": [{"x": [0, 1, 2], "y": [0, 1, 0], "kind": "line"}],
            },
        ]
        return json.dumps(payload)
