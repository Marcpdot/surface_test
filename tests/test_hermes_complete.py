from __future__ import annotations

from pathlib import Path

import pytest

from surface.hermes_bridge import HermesBridge, is_structured_input, unwrap_model_output
from surface.hermes_transport import FakeTransport
from surface.protocol import LayoutCommand, ProtocolError, TextCommand

_EVAL = Path(__file__).resolve().parent / "eval" / "fixtures"


def test_is_structured_input() -> None:
    assert is_structured_input('  {"type":"text"}')
    assert is_structured_input("[]")
    assert not is_structured_input("forklar gradient")


def test_unwrap_plain_json() -> None:
    raw = ' {"type":"text","id":"a","content":"x"} '
    assert unwrap_model_output(raw).startswith("{")


def test_unwrap_single_json_fence() -> None:
    raw = '```json\n{"type":"text","id":"a","content":"x"}\n```'
    assert unwrap_model_output(raw) == '{"type":"text","id":"a","content":"x"}'


def test_complete_good_json() -> None:
    transport = FakeTransport(
        output='{"type":"text","id":"h-1","content":"hei"}'
    )
    commands = HermesBridge().complete("forklar", transport)
    assert commands == [
        TextCommand(type="text", id="h-1", content="hei", format="markdown")
    ]
    assert "User:\nforklar" in transport.prompts[0]


def test_complete_fenced_json() -> None:
    transport = FakeTransport(
        output='```json\n{"type":"text","id":"h-1","content":"hei"}\n```\n'
    )
    commands = HermesBridge().complete("hei", transport)
    assert commands[0].id == "h-1"


def test_complete_prose_cannot_translate() -> None:
    transport = FakeTransport(output="here is an explanation without json")
    with pytest.raises(ProtocolError) as exc_info:
        HermesBridge().complete("forklar", transport)
    assert exc_info.value.code == "cannot_translate"


def test_complete_empty_output() -> None:
    transport = FakeTransport(output="   ")
    with pytest.raises(ProtocolError) as exc_info:
        HermesBridge().complete("forklar", transport)
    assert exc_info.value.code == "cannot_translate"


def test_complete_does_not_invent_fields() -> None:
    transport = FakeTransport(
        output='{"type":"text","id":"h-1","content":"x","note":"nope"}'
    )
    with pytest.raises(ProtocolError) as exc_info:
        HermesBridge().complete("x", transport)
    assert exc_info.value.code == "unknown_field"


def test_complete_empty_user_text() -> None:
    with pytest.raises(ProtocolError) as exc_info:
        HermesBridge().complete("  ", FakeTransport(output="{}"))
    assert exc_info.value.code == "empty_field"


def test_eval_fixture_layout_children_exist() -> None:
    raw = (_EVAL / "04_layout.json").read_text(encoding="utf-8")
    commands = HermesBridge().complete("ignored", FakeTransport(output=raw))
    types = [c.type for c in commands]
    assert "text" in types
    assert "plot" in types
    assert "layout" in types
    layout = next(c for c in commands if isinstance(c, LayoutCommand))
    ids = {c.id for c in commands}
    assert set(layout.children) <= ids


@pytest.mark.parametrize(
    "name",
    [
        "01_text.json",
        "02_text_equation.json",
        "03_text_plot.json",
        "04_layout.json",
    ],
)
def test_eval_fixtures_parse(name: str) -> None:
    raw = (_EVAL / name).read_text(encoding="utf-8")
    commands = HermesBridge().from_hermes_output(raw)
    assert commands


def test_eval_invalid_fixture_rejected() -> None:
    raw = (_EVAL / "05_invalid.json").read_text(encoding="utf-8")
    with pytest.raises(ProtocolError):
        HermesBridge().from_hermes_output(raw)
