# Qt-free by design.
from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping

from surface.hermes_prompt import build_prompt
from surface.hermes_transport import HermesTransport
from surface.protocol import (
    ID_PATTERN,
    MAX_TEXT_LENGTH,
    Command,
    ProtocolError,
    TextCommand,
    parse_command_list,
)

_LOG = logging.getLogger("surface.hermes")
_RAW_PREVIEW = 240

_JSON_FENCE = re.compile(
    r"^```(?:json)?\s*\n(.*)\n```\s*$",
    re.DOTALL | re.IGNORECASE,
)


def is_structured_input(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") or stripped.startswith("[")


def unwrap_model_output(raw: str) -> str:
    stripped = raw.strip()
    match = _JSON_FENCE.fullmatch(stripped)
    if match is not None:
        return match.group(1).strip()
    return stripped


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

    def from_user_input(self, text: str, *, text_id: str = "") -> list[Command]:
        """Local/debug structured input only. ``text_id`` is ignored.

        Stripped text starting with '{' or '[' → from_hermes_output.
        Otherwise → ProtocolError(cannot_translate). Empty → empty_field.
        Natural language belongs to complete().
        """
        stripped = text.strip()
        if not stripped:
            raise ProtocolError("empty_field", "empty input")
        if not is_structured_input(stripped):
            raise ProtocolError("cannot_translate", "cannot translate Hermes output")
        return self.from_hermes_output(stripped)

    def complete(
        self,
        text: str,
        transport: HermesTransport,
        workspace_snapshot: Mapping[str, object] | None = None,
        study_context: Mapping[str, object] | None = None,
    ) -> list[Command]:
        """Send natural language to Hermes and translate its bounded response."""
        stripped = text.strip()
        if not stripped:
            raise ProtocolError("empty_field", "empty input")
        raw = transport.complete(
            build_prompt(stripped, workspace_snapshot, study_context)
        )
        try:
            if study_context is not None:
                return _build_study_command(raw, study_context)
            unwrapped = unwrap_model_output(raw)
            if not unwrapped:
                raise ProtocolError(
                    "cannot_translate", "cannot translate Hermes output"
                )
            return self.from_hermes_output(unwrapped)
        except ProtocolError as exc:
            decode_error = exc.__cause__
            if exc.code == "invalid_json" and isinstance(
                decode_error, json.JSONDecodeError
            ):
                _LOG.warning(
                    "invalid_json: %s (line %d, column %d, character position %d)",
                    decode_error.msg,
                    decode_error.lineno,
                    decode_error.colno,
                    decode_error.pos,
                )
            _LOG.warning("%s: raw Hermes stdout:\n%s", exc.code, raw)
            if exc.code != "cannot_translate":
                raise
            preview = raw.strip()[:_RAW_PREVIEW]
            raise ProtocolError(
                "cannot_translate",
                f"cannot translate Hermes output: {preview}",
                command_id=exc.command_id,
            ) from exc

    @staticmethod
    def demo_output(*, image_source: str) -> str:
        """json.dumps of primitives plus study layouts."""
        payload = [
            {
                "type": "text",
                "id": "problem-1",
                "content": (
                    "## Bending stress\nA rectangular beam section has width "
                    "$b=50\\,\\mathrm{mm}$, height $h=100\\,\\mathrm{mm}$, and bending "
                    "moment $M=5\\,\\mathrm{kN\\,m}$. Find the maximum bending stress. "
                    "Use $I=bh^3/12$ and consistent units."
                ),
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


def _build_study_command(
    output: str, study_context: Mapping[str, object]
) -> list[Command]:
    response_id, max_chars = _study_response_contract(study_context)
    if not output.strip():
        raise ProtocolError("invalid_study_response", "study response content is empty")
    if len(output) > max_chars:
        raise ProtocolError(
            "limit_exceeded",
            f"study response exceeds {max_chars} characters",
            command_id=response_id,
        )
    return [
        TextCommand(type="text", id=response_id, content=output, format="markdown")
    ]


def _study_response_contract(
    study_context: Mapping[str, object],
) -> tuple[str, int]:
    study = study_context.get("study")
    response = study.get("response") if isinstance(study, Mapping) else None
    if not isinstance(response, Mapping) or response.get("type") != "text":
        raise ProtocolError(
            "invalid_study_context", "study response contract must require text"
        )
    response_id = response.get("id")
    if not isinstance(response_id, str) or re.fullmatch(ID_PATTERN, response_id) is None:
        raise ProtocolError(
            "invalid_study_context", "study response contract has an invalid id"
        )
    max_chars = response.get("max_chars", MAX_TEXT_LENGTH)
    if (
        isinstance(max_chars, bool)
        or not isinstance(max_chars, int)
        or not 0 < max_chars <= MAX_TEXT_LENGTH
    ):
        raise ProtocolError(
            "invalid_study_context", "study response contract has an invalid limit"
        )
    return response_id, max_chars
