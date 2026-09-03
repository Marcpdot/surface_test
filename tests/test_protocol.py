import json

import pytest

from surface.protocol import (
    EquationCommand,
    ImageCommand,
    PlotCommand,
    ProtocolError,
    Series,
    TextCommand,
    parse_command,
    parse_command_list,
)

TEXT = {
    "type": "text",
    "id": "t-1",
    "content": "## Bjelketeori\nBøyespanning dekkes av equation-block.",
    "format": "markdown",
}
EQUATION = {
    "type": "equation",
    "id": "eq-1",
    "latex": r"\sigma = \frac{My}{I}",
    "display": "block",
}
IMAGE = {
    "type": "image",
    "id": "img-1",
    "source": r"C:\course\beam.png",
    "alt": "Bjelke tverrsnitt",
}
PLOT = {
    "type": "plot",
    "id": "plot-1",
    "title": "Moment langs bjelke",
    "xlabel": "x [m]",
    "ylabel": "M [Nm]",
    "series": [
        {
            "label": "lasttilfelle A",
            "kind": "line",
            "x": [0, 1, 2, 3],
            "y": [0, 12.5, 12.5, 0],
        }
    ],
}


def _error(payload, *, list_parse: bool = False) -> ProtocolError:
    func = parse_command_list if list_parse else parse_command
    with pytest.raises(ProtocolError) as exc_info:
        func(payload)
    return exc_info.value


def test_valid_text_command() -> None:
    command = parse_command(TEXT)
    assert command == TextCommand(
        type="text",
        id="t-1",
        content="## Bjelketeori\nBøyespanning dekkes av equation-block.",
        format="markdown",
    )


def test_valid_equation_command() -> None:
    command = parse_command(EQUATION)
    assert command == EquationCommand(
        type="equation",
        id="eq-1",
        latex=r"\sigma = \frac{My}{I}",
        display="block",
    )


def test_valid_image_command() -> None:
    command = parse_command(IMAGE)
    assert command == ImageCommand(
        type="image",
        id="img-1",
        source=r"C:\course\beam.png",
        alt="Bjelke tverrsnitt",
    )


def test_image_source_is_not_checked_for_existence() -> None:
    command = parse_command(
        {"type": "image", "id": "img-missing", "source": "definitely-missing.png"}
    )
    assert command.source == "definitely-missing.png"


def test_valid_plot_command() -> None:
    command = parse_command(PLOT)
    assert command == PlotCommand(
        type="plot",
        id="plot-1",
        series=(
            Series(
                x=(0.0, 1.0, 2.0, 3.0),
                y=(0.0, 12.5, 12.5, 0.0),
                label="lasttilfelle A",
                kind="line",
            ),
        ),
        title="Moment langs bjelke",
        xlabel="x [m]",
        ylabel="M [Nm]",
    )


def test_text_equation_image_plot_defaults() -> None:
    text = parse_command({"type": "text", "id": "t-1", "content": "hei"})
    assert text.format == "markdown"
    equation = parse_command({"type": "equation", "id": "eq-1", "latex": "a + b"})
    assert equation.display == "block"
    image = parse_command({"type": "image", "id": "img-1", "source": "beam.png"})
    assert image.alt == ""
    plot = parse_command(
        {"type": "plot", "id": "p-1", "series": [{"x": [1], "y": [2]}]}
    )
    assert plot.title == ""
    assert plot.xlabel == ""
    assert plot.ylabel == ""
    assert plot.series[0].label == ""
    assert plot.series[0].kind == "line"


@pytest.mark.parametrize("kind", ["line", "scatter", "bar"])
def test_plot_series_kinds(kind: str) -> None:
    command = parse_command(
        {
            "type": "plot",
            "id": "p-1",
            "series": [{"x": [0, 1], "y": [1, 0], "kind": kind}],
        }
    )
    assert command.series[0].kind == kind


def test_parse_command_json_string() -> None:
    command = parse_command(json.dumps(TEXT))
    assert isinstance(command, TextCommand)
    assert command.id == "t-1"


def test_parse_command_bytes_with_bom() -> None:
    payload = json.dumps(EQUATION).encode("utf-8-sig")
    assert payload.startswith(b"\xef\xbb\xbf")
    command = parse_command(payload)
    assert isinstance(command, EquationCommand)
    assert command.id == "eq-1"


def test_parse_command_already_dict() -> None:
    command = parse_command(dict(IMAGE))
    assert isinstance(command, ImageCommand)
    assert command.id == "img-1"


def test_parse_command_list_from_list() -> None:
    commands = parse_command_list([TEXT, EQUATION])
    assert [item.id for item in commands] == ["t-1", "eq-1"]
    assert isinstance(commands[0], TextCommand)
    assert isinstance(commands[1], EquationCommand)


def test_parse_command_list_from_commands_wrapper() -> None:
    commands = parse_command_list({"commands": [IMAGE, PLOT]})
    assert [item.id for item in commands] == ["img-1", "plot-1"]
    assert isinstance(commands[0], ImageCommand)
    assert isinstance(commands[1], PlotCommand)


def test_parse_command_list_single_object() -> None:
    commands = parse_command_list(TEXT)
    assert len(commands) == 1
    assert commands[0].id == "t-1"


def test_parse_command_list_json_array_string() -> None:
    commands = parse_command_list(json.dumps([TEXT]))
    assert len(commands) == 1
    assert isinstance(commands[0], TextCommand)


def test_parse_command_list_fail_fast() -> None:
    error = _error(
        [
            {"type": "text", "id": "t-1", "content": "ok"},
            {"type": "nope", "id": "t-2", "content": "x"},
        ],
        list_parse=True,
    )
    assert error.code == "unknown_type"
    assert error.command_id == "t-2"


def test_commands_wrapper_illegal_when_type_is_set() -> None:
    error = _error(
        {
            "type": "text",
            "id": "t-1",
            "content": "x",
            "commands": [],
        },
        list_parse=True,
    )
    assert error.code == "unknown_field"


def test_commands_wrapper_rejects_unknown_field() -> None:
    error = _error({"commands": [TEXT], "extra": 1}, list_parse=True)
    assert error.code == "unknown_field"


def test_unknown_type() -> None:
    error = _error({"type": "widget", "id": "w-1"})
    assert error.code == "unknown_type"
    assert error.command_id == "w-1"


def test_unknown_field_top_level() -> None:
    error = _error({**TEXT, "note": "nope"})
    assert error.code == "unknown_field"
    assert error.command_id == "t-1"


@pytest.mark.parametrize("extra", ["color", "code"])
def test_unknown_field_in_series(extra: str) -> None:
    series = {"x": [0, 1], "y": [1, 0], extra: "red"}
    error = _error({"type": "plot", "id": "p-1", "series": [series]})
    assert error.code == "unknown_field"
    assert error.command_id == "p-1"


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "t-1", "content": "x"},
        {"type": "text", "content": "x"},
        {"type": "text", "id": "t-1"},
        {"type": "equation", "id": "eq-1"},
        {"type": "image", "id": "img-1"},
        {"type": "plot", "id": "p-1"},
        {"type": "plot", "id": "p-1", "series": [{"y": [1]}]},
        {"type": "plot", "id": "p-1", "series": [{"x": [1]}]},
    ],
)
def test_missing_fields(payload: dict) -> None:
    error = _error(payload)
    assert error.code == "missing_field"


@pytest.mark.parametrize(
    "ident",
    [
        "",
        " ",
        "id with space",
        "A" + "a" * 64,
        "-leading",
        ".dot",
        "_under",
    ],
)
def test_invalid_id(ident: str) -> None:
    error = _error({"type": "text", "id": ident, "content": "x"})
    assert error.code == "invalid_id"
    assert error.command_id == ident


def test_valid_id_max_length() -> None:
    ident = "A" + "a" * 63
    command = parse_command({"type": "text", "id": ident, "content": "x"})
    assert command.id == ident


def test_dollar_in_latex() -> None:
    error = _error({"type": "equation", "id": "eq-1", "latex": r"$\sigma$"})
    assert error.code == "invalid_field"


def test_bool_in_series() -> None:
    error = _error(
        {"type": "plot", "id": "p-1", "series": [{"x": [0, True], "y": [0, 1]}]}
    )
    assert error.code == "invalid_field"


def test_false_in_series() -> None:
    error = _error(
        {"type": "plot", "id": "p-1", "series": [{"x": [0, 1], "y": [False, 1]}]}
    )
    assert error.code == "invalid_field"


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_nan_inf_in_series(token: str) -> None:
    payload = (
        '{"type":"plot","id":"p-1","series":[{"x":[0, %s],"y":[0, 1]}]}' % token
    )
    error = _error(payload)
    assert error.code == "invalid_field"


def test_nan_inf_from_python_floats() -> None:
    error = _error(
        {
            "type": "plot",
            "id": "p-1",
            "series": [{"x": [0.0, float("nan")], "y": [0.0, 1.0]}],
        }
    )
    assert error.code == "invalid_field"
    error = _error(
        {
            "type": "plot",
            "id": "p-1",
            "series": [{"x": [0.0, float("inf")], "y": [0.0, 1.0]}],
        }
    )
    assert error.code == "invalid_field"


def test_int_coerced_to_float() -> None:
    command = parse_command(
        {"type": "plot", "id": "p-1", "series": [{"x": [0, 1, 2], "y": [0, 12, 0]}]}
    )
    assert command.series[0].x == (0.0, 1.0, 2.0)
    assert command.series[0].y == (0.0, 12.0, 0.0)
    assert all(type(value) is float for value in command.series[0].x)
    assert all(type(value) is float for value in command.series[0].y)


def test_whitespace_stripped_storage() -> None:
    text = parse_command({"type": "text", "id": "t-1", "content": "  hello  "})
    assert text.content == "hello"
    equation = parse_command({"type": "equation", "id": "eq-1", "latex": "  a+b  "})
    assert equation.latex == "a+b"
    image = parse_command(
        {
            "type": "image",
            "id": "img-1",
            "source": "  beam.png  ",
            "alt": "  alt  ",
        }
    )
    assert image.source == "beam.png"
    assert image.alt == "alt"
    plot = parse_command(
        {
            "type": "plot",
            "id": "p-1",
            "title": "  T  ",
            "xlabel": "  X  ",
            "ylabel": "  Y  ",
            "series": [{"x": [1], "y": [2], "label": "  L  "}],
        }
    )
    assert plot.title == "T"
    assert plot.xlabel == "X"
    assert plot.ylabel == "Y"
    assert plot.series[0].label == "L"


def test_xy_length_mismatch() -> None:
    error = _error(
        {"type": "plot", "id": "p-1", "series": [{"x": [0, 1], "y": [0]}]}
    )
    assert error.code == "invalid_field"


def test_zero_series() -> None:
    error = _error({"type": "plot", "id": "p-1", "series": []})
    assert error.code == "empty_field"


def test_nine_series() -> None:
    series = [{"x": [0], "y": [1]} for _ in range(9)]
    error = _error({"type": "plot", "id": "p-1", "series": series})
    assert error.code == "limit_exceeded"


def test_eight_series_ok() -> None:
    series = [{"x": [0], "y": [1]} for _ in range(8)]
    command = parse_command({"type": "plot", "id": "p-1", "series": series})
    assert len(command.series) == 8


def test_10001_points() -> None:
    xs = list(range(10_001))
    ys = list(range(10_001))
    error = _error({"type": "plot", "id": "p-1", "series": [{"x": xs, "y": ys}]})
    assert error.code == "limit_exceeded"


def test_10000_points_ok() -> None:
    xs = list(range(10_000))
    ys = list(range(10_000))
    command = parse_command(
        {"type": "plot", "id": "p-1", "series": [{"x": xs, "y": ys}]}
    )
    assert len(command.series[0].x) == 10_000


def test_invalid_json() -> None:
    error = _error("{")
    assert error.code == "invalid_json"
    error = _error(b"\xff\xfe not utf-8")
    assert error.code == "invalid_json"


def test_not_object() -> None:
    error = _error("[1]")
    assert error.code == "not_object"
    error = _error("1")
    assert error.code == "not_object"
    error = _error("null", list_parse=True)
    assert error.code == "not_object"


def test_empty_content_latex_source() -> None:
    assert _error({"type": "text", "id": "t-1", "content": "   "}).code == "empty_field"
    assert _error({"type": "equation", "id": "eq-1", "latex": ""}).code == "empty_field"
    assert _error({"type": "image", "id": "img-1", "source": " "}).code == "empty_field"


def test_invalid_enum_fields() -> None:
    assert (
        _error({"type": "text", "id": "t-1", "content": "x", "format": "html"}).code
        == "invalid_field"
    )
    assert (
        _error(
            {"type": "equation", "id": "eq-1", "latex": "a", "display": "wide"}
        ).code
        == "invalid_field"
    )
    assert (
        _error(
            {
                "type": "plot",
                "id": "p-1",
                "series": [{"x": [1], "y": [2], "kind": "area"}],
            }
        ).code
        == "invalid_field"
    )


def test_limit_exceeded_text() -> None:
    error = _error({"type": "text", "id": "t-1", "content": "x" * 50_001})
    assert error.code == "limit_exceeded"


def test_id_attached_when_readable() -> None:
    error = _error({"type": "text", "id": "t-1"})
    assert error.code == "missing_field"
    assert error.command_id == "t-1"


def test_plain_format_and_inline_display() -> None:
    text = parse_command(
        {"type": "text", "id": "t-1", "content": "raw", "format": "plain"}
    )
    assert text.format == "plain"
    equation = parse_command(
        {"type": "equation", "id": "eq-1", "latex": "a", "display": "inline"}
    )
    assert equation.display == "inline"
