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
                "id": "problem-1",
                "content": "## Bending stress\nFind $\\sigma$ for the beam.",
                "format": "markdown",
            },
            {
                "type": "image",
                "id": "figure-1",
                "source": image_source,
                "alt": "beam diagram",
            },
            {
                "type": "equation",
                "id": "equation-1",
                "latex": r"\sigma = \frac{My}{I}",
            },
            {
                "type": "plot",
                "id": "plot-1",
                "title": "Moment along beam",
                "xlabel": "x",
                "ylabel": "M",
                "series": [{"x": [0, 1, 2], "y": [0, 1, 0], "kind": "line"}],
            },
            {
                "type": "layout",
                "id": "row-problem",
                "direction": "horizontal",
                "children": ["problem-1", "figure-1"],
            },
            {
                "type": "layout",
                "id": "row-model",
                "direction": "horizontal",
                "children": ["equation-1", "plot-1"],
            },
            {
                "type": "layout",
                "id": "study-1",
                "direction": "vertical",
                "children": ["row-problem", "row-model"],
            },
        ]
        return json.dumps(payload)
