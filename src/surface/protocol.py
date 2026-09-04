# Qt-free by design.
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Literal, Union

CommandType = Literal["text", "equation", "image", "plot", "layout", "move", "remove"]
TextFormat = Literal["markdown", "plain"]
EquationDisplay = Literal["block", "inline"]
SeriesKind = Literal["line", "scatter", "bar"]
LayoutDirection = Literal["vertical", "horizontal"]

MAX_ID_LENGTH = 64
MAX_TEXT_LENGTH = 50_000
MAX_LATEX_LENGTH = 5_000
MAX_ALT_LENGTH = 500
MAX_SERIES = 8
MAX_POINTS = 10_000
MAX_CHILDREN = 8
ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"

_ID_RE = re.compile(ID_PATTERN)
_MAX_TITLE_LENGTH = 200
_MAX_AXIS_LABEL_LENGTH = 100
_MAX_SERIES_LABEL_LENGTH = 80
_TEXT_FIELDS = frozenset({"type", "id", "content", "format"})
_EQUATION_FIELDS = frozenset({"type", "id", "latex", "display"})
_IMAGE_FIELDS = frozenset({"type", "id", "source", "alt"})
_PLOT_FIELDS = frozenset({"type", "id", "series", "title", "xlabel", "ylabel"})
_LAYOUT_FIELDS = frozenset({"type", "id", "direction", "children"})
_MOVE_FIELDS = frozenset({"type", "id", "parent", "index"})
_REMOVE_FIELDS = frozenset({"type", "id"})
_SERIES_FIELDS = frozenset({"x", "y", "label", "kind"})
_ALLOWED_FIELDS = {
    "text": _TEXT_FIELDS,
    "equation": _EQUATION_FIELDS,
    "image": _IMAGE_FIELDS,
    "plot": _PLOT_FIELDS,
    "layout": _LAYOUT_FIELDS,
    "move": _MOVE_FIELDS,
    "remove": _REMOVE_FIELDS,
}


class ProtocolError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        command_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.command_id = command_id


@dataclass(frozen=True)
class TextCommand:
    type: Literal["text"]
    id: str
    content: str
    format: TextFormat = "markdown"


@dataclass(frozen=True)
class EquationCommand:
    type: Literal["equation"]
    id: str
    latex: str
    display: EquationDisplay = "block"


@dataclass(frozen=True)
class ImageCommand:
    type: Literal["image"]
    id: str
    source: str
    alt: str = ""


@dataclass(frozen=True)
class Series:
    x: tuple[float, ...]
    y: tuple[float, ...]
    label: str = ""
    kind: SeriesKind = "line"


@dataclass(frozen=True)
class PlotCommand:
    type: Literal["plot"]
    id: str
    series: tuple[Series, ...]
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""


@dataclass(frozen=True)
class LayoutCommand:
    type: Literal["layout"]
    id: str
    direction: LayoutDirection
    children: tuple[str, ...]


@dataclass(frozen=True)
class MoveCommand:
    type: Literal["move"]
    id: str
    parent: str | None
    index: int | None = None


@dataclass(frozen=True)
class RemoveCommand:
    type: Literal["remove"]
    id: str


NodeCommand = Union[TextCommand, EquationCommand, ImageCommand, PlotCommand, LayoutCommand]
Command = Union[NodeCommand, MoveCommand, RemoveCommand]


def parse_command(payload: str | bytes | dict[str, Any]) -> Command:
    """Parse exactly one command object.

    Raises:
        ProtocolError: invalid JSON, unknown type/field, failed validation.
    """
    return _parse_command_object(_loads(payload))


def parse_command_list(payload: str | bytes | list[Any] | dict[str, Any]) -> list[Command]:
    """Parse one command, a JSON array of commands, or ``{"commands": [...]}``.

    Raises:
        ProtocolError: on the first invalid element (fail-fast, ingen delvis liste).
    """
    loaded = _loads(payload)
    if isinstance(loaded, list):
        return [_parse_command_object(item) for item in loaded]
    if isinstance(loaded, dict):
        if "type" in loaded:
            return [_parse_command_object(loaded)]
        if "commands" in loaded:
            return _parse_commands_wrapper(loaded)
        return [_parse_command_object(loaded)]
    raise ProtocolError("not_object", "payload is not a JSON object or array")


def _loads(payload: str | bytes | dict[str, Any] | list[Any] | Any) -> Any:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ProtocolError("invalid_json", "payload is not valid UTF-8") from exc
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProtocolError("invalid_json", "invalid JSON") from exc
    return payload


def _readable_id(obj: dict[str, Any]) -> str | None:
    value = obj.get("id")
    return value if isinstance(value, str) else None


def _reject_unknown(
    obj: dict[str, Any],
    allowed: frozenset[str],
    *,
    command_id: str | None,
) -> None:
    for key in obj:
        if key not in allowed:
            raise ProtocolError(
                "unknown_field",
                f"unknown field {key!r}",
                command_id=command_id,
            )


def _parse_commands_wrapper(obj: dict[str, Any]) -> list[Command]:
    _reject_unknown(obj, frozenset({"commands"}), command_id=None)
    commands = obj["commands"]
    if not isinstance(commands, list):
        raise ProtocolError("invalid_field", "invalid field 'commands'")
    return [_parse_command_object(item) for item in commands]


def _parse_command_object(obj: Any) -> Command:
    if not isinstance(obj, dict):
        raise ProtocolError("not_object", "payload is not a JSON object")
    command_id = _readable_id(obj)
    if "type" not in obj:
        raise ProtocolError("missing_field", "missing field 'type'", command_id=command_id)
    type_value = obj["type"]
    if not isinstance(type_value, str):
        raise ProtocolError("invalid_field", "invalid field 'type'", command_id=command_id)
    allowed = _ALLOWED_FIELDS.get(type_value)
    if allowed is None:
        raise ProtocolError(
            "unknown_type",
            f"unknown type {type_value!r}",
            command_id=command_id,
        )
    _reject_unknown(obj, allowed, command_id=command_id)
    ident = _require_id(obj, command_id=command_id)
    if type_value == "text":
        return _parse_text(obj, ident)
    if type_value == "equation":
        return _parse_equation(obj, ident)
    if type_value == "image":
        return _parse_image(obj, ident)
    if type_value == "layout":
        return _parse_layout(obj, ident)
    if type_value == "move":
        return _parse_move(obj, ident)
    if type_value == "remove":
        return RemoveCommand(type="remove", id=ident)
    return _parse_plot(obj, ident)


def _require_id(obj: dict[str, Any], *, command_id: str | None) -> str:
    if "id" not in obj:
        raise ProtocolError("missing_field", "missing field 'id'", command_id=command_id)
    ident = obj["id"]
    if not isinstance(ident, str):
        raise ProtocolError("invalid_field", "invalid field 'id'", command_id=None)
    if _ID_RE.fullmatch(ident) is None:
        raise ProtocolError("invalid_id", f"invalid id {ident!r}", command_id=ident)
    return ident


def _required_stripped(
    obj: dict[str, Any],
    key: str,
    *,
    max_length: int | None,
    command_id: str,
) -> str:
    if key not in obj:
        raise ProtocolError("missing_field", f"missing field {key!r}", command_id=command_id)
    value = obj[key]
    if not isinstance(value, str):
        raise ProtocolError("invalid_field", f"invalid field {key!r}", command_id=command_id)
    stripped = value.strip()
    if not stripped:
        raise ProtocolError("empty_field", f"empty field {key!r}", command_id=command_id)
    if max_length is not None and len(stripped) > max_length:
        raise ProtocolError(
            "limit_exceeded",
            f"field {key!r} exceeds limit of {max_length}",
            command_id=command_id,
        )
    return stripped


def _optional_stripped(
    obj: dict[str, Any],
    key: str,
    *,
    max_length: int,
    command_id: str,
) -> str:
    if key not in obj:
        return ""
    value = obj[key]
    if not isinstance(value, str):
        raise ProtocolError("invalid_field", f"invalid field {key!r}", command_id=command_id)
    stripped = value.strip()
    if len(stripped) > max_length:
        raise ProtocolError(
            "limit_exceeded",
            f"field {key!r} exceeds limit of {max_length}",
            command_id=command_id,
        )
    return stripped


def _parse_text(obj: dict[str, Any], command_id: str) -> TextCommand:
    content = _required_stripped(
        obj, "content", max_length=MAX_TEXT_LENGTH, command_id=command_id
    )
    fmt: TextFormat = "markdown"
    if "format" in obj:
        value = obj["format"]
        if value not in ("markdown", "plain"):
            raise ProtocolError("invalid_field", "invalid field 'format'", command_id=command_id)
        fmt = value
    return TextCommand(type="text", id=command_id, content=content, format=fmt)


def _parse_equation(obj: dict[str, Any], command_id: str) -> EquationCommand:
    latex = _required_stripped(
        obj, "latex", max_length=MAX_LATEX_LENGTH, command_id=command_id
    )
    if "$" in latex:
        raise ProtocolError("invalid_field", "invalid field 'latex'", command_id=command_id)
    display: EquationDisplay = "block"
    if "display" in obj:
        value = obj["display"]
        if value not in ("block", "inline"):
            raise ProtocolError(
                "invalid_field", "invalid field 'display'", command_id=command_id
            )
        display = value
    return EquationCommand(type="equation", id=command_id, latex=latex, display=display)


def _parse_image(obj: dict[str, Any], command_id: str) -> ImageCommand:
    source = _required_stripped(obj, "source", max_length=None, command_id=command_id)
    alt = _optional_stripped(obj, "alt", max_length=MAX_ALT_LENGTH, command_id=command_id)
    return ImageCommand(type="image", id=command_id, source=source, alt=alt)


def _parse_layout(obj: dict[str, Any], command_id: str) -> LayoutCommand:
    if "direction" not in obj:
        raise ProtocolError(
            "missing_field", "missing field 'direction'", command_id=command_id
        )
    direction = obj["direction"]
    if direction not in ("vertical", "horizontal"):
        raise ProtocolError(
            "invalid_field", "invalid field 'direction'", command_id=command_id
        )
    if "children" not in obj:
        raise ProtocolError(
            "missing_field", "missing field 'children'", command_id=command_id
        )
    children_value = obj["children"]
    if not isinstance(children_value, list):
        raise ProtocolError(
            "invalid_field", "invalid field 'children'", command_id=command_id
        )
    if not children_value:
        raise ProtocolError(
            "empty_field", "empty field 'children'", command_id=command_id
        )
    if len(children_value) > MAX_CHILDREN:
        raise ProtocolError(
            "limit_exceeded",
            f"field 'children' exceeds limit of {MAX_CHILDREN}",
            command_id=command_id,
        )
    children: list[str] = []
    seen: set[str] = set()
    for item in children_value:
        if not isinstance(item, str):
            raise ProtocolError(
                "invalid_field", "invalid field 'children'", command_id=command_id
            )
        if _ID_RE.fullmatch(item) is None:
            raise ProtocolError(
                "invalid_id", f"invalid id {item!r}", command_id=command_id
            )
        if item in seen:
            raise ProtocolError(
                "duplicate_child",
                f"duplicate child {item!r}",
                command_id=command_id,
            )
        seen.add(item)
        children.append(item)
    return LayoutCommand(
        type="layout",
        id=command_id,
        direction=direction,
        children=tuple(children),
    )


def _parse_move(obj: dict[str, Any], command_id: str) -> MoveCommand:
    if "parent" not in obj:
        raise ProtocolError(
            "missing_field", "missing field 'parent'", command_id=command_id
        )
    parent = obj["parent"]
    if parent is not None:
        if not isinstance(parent, str):
            raise ProtocolError(
                "invalid_field", "invalid field 'parent'", command_id=command_id
            )
        if _ID_RE.fullmatch(parent) is None:
            raise ProtocolError(
                "invalid_id", f"invalid id {parent!r}", command_id=command_id
            )

    index: int | None = None
    if "index" in obj:
        value = obj["index"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProtocolError(
                "invalid_field", "invalid field 'index'", command_id=command_id
            )
        index = value
    return MoveCommand(type="move", id=command_id, parent=parent, index=index)


def _parse_plot(obj: dict[str, Any], command_id: str) -> PlotCommand:
    if "series" not in obj:
        raise ProtocolError("missing_field", "missing field 'series'", command_id=command_id)
    series_value = obj["series"]
    if not isinstance(series_value, list):
        raise ProtocolError("invalid_field", "invalid field 'series'", command_id=command_id)
    if not series_value:
        raise ProtocolError("empty_field", "empty field 'series'", command_id=command_id)
    if len(series_value) > MAX_SERIES:
        raise ProtocolError(
            "limit_exceeded",
            f"field 'series' exceeds limit of {MAX_SERIES}",
            command_id=command_id,
        )
    series = tuple(_parse_series(item, command_id=command_id) for item in series_value)
    title = _optional_stripped(
        obj, "title", max_length=_MAX_TITLE_LENGTH, command_id=command_id
    )
    xlabel = _optional_stripped(
        obj, "xlabel", max_length=_MAX_AXIS_LABEL_LENGTH, command_id=command_id
    )
    ylabel = _optional_stripped(
        obj, "ylabel", max_length=_MAX_AXIS_LABEL_LENGTH, command_id=command_id
    )
    return PlotCommand(
        type="plot",
        id=command_id,
        series=series,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
    )


def _parse_series(obj: Any, *, command_id: str) -> Series:
    if not isinstance(obj, dict):
        raise ProtocolError("not_object", "series item is not a JSON object", command_id=command_id)
    _reject_unknown(obj, _SERIES_FIELDS, command_id=command_id)
    x_values = _parse_points(obj, "x", command_id=command_id)
    y_values = _parse_points(obj, "y", command_id=command_id)
    if len(x_values) != len(y_values):
        raise ProtocolError(
            "invalid_field",
            "fields 'x' and 'y' must have the same length",
            command_id=command_id,
        )
    label = _optional_stripped(
        obj, "label", max_length=_MAX_SERIES_LABEL_LENGTH, command_id=command_id
    )
    kind: SeriesKind = "line"
    if "kind" in obj:
        value = obj["kind"]
        if value not in ("line", "scatter", "bar"):
            raise ProtocolError("invalid_field", "invalid field 'kind'", command_id=command_id)
        kind = value
    return Series(x=x_values, y=y_values, label=label, kind=kind)


def _parse_points(obj: dict[str, Any], key: str, *, command_id: str) -> tuple[float, ...]:
    if key not in obj:
        raise ProtocolError("missing_field", f"missing field {key!r}", command_id=command_id)
    value = obj[key]
    if not isinstance(value, list):
        raise ProtocolError("invalid_field", f"invalid field {key!r}", command_id=command_id)
    if not value:
        raise ProtocolError("empty_field", f"empty field {key!r}", command_id=command_id)
    if len(value) > MAX_POINTS:
        raise ProtocolError(
            "limit_exceeded",
            f"field {key!r} exceeds limit of {MAX_POINTS}",
            command_id=command_id,
        )
    return tuple(_finite_float(item, field=key, command_id=command_id) for item in value)


def _finite_float(value: Any, *, field: str, command_id: str) -> float:
    # bool is an int subclass; reject before coercing to float.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolError("invalid_field", f"invalid field {field!r}", command_id=command_id)
    try:
        number = float(value)
    except OverflowError:
        raise ProtocolError(
            "invalid_field", f"invalid field {field!r}", command_id=command_id
        ) from None
    if not math.isfinite(number):
        raise ProtocolError("invalid_field", f"invalid field {field!r}", command_id=command_id)
    return number
