from __future__ import annotations

import sys
from pathlib import Path

import pytest

from surface.hermes_transport import (
    CommandTransport,
    FakeTransport,
    transport_from_env,
)
from surface.protocol import ProtocolError

_STUB = str(Path(__file__).resolve().parent / "fake_hermes.py")


def test_fake_transport_returns_output() -> None:
    transport = FakeTransport(output='{"type":"text","id":"a","content":"x"}')
    assert transport.complete("hello") == '{"type":"text","id":"a","content":"x"}'
    assert transport.prompts == ["hello"]


def test_fake_transport_raises_configured_error() -> None:
    err = ProtocolError("hermes_failed", "boom")
    transport = FakeTransport(error=err)
    with pytest.raises(ProtocolError) as exc_info:
        transport.complete("hello")
    assert exc_info.value.code == "hermes_failed"


def test_transport_from_env_missing() -> None:
    assert transport_from_env({}) is None
    assert transport_from_env({"SURFACE_HERMES_CMD": "  "}) is None


def test_command_transport_stub_ok() -> None:
    transport = CommandTransport([sys.executable, _STUB], timeout_s=10)
    out = transport.complete("prompt")
    assert '"stub-1"' in out


def test_command_transport_stub_fail() -> None:
    transport = CommandTransport([sys.executable, _STUB, "--fail"], timeout_s=10)
    with pytest.raises(ProtocolError) as exc_info:
        transport.complete("prompt")
    assert exc_info.value.code == "hermes_failed"


def test_command_transport_timeout() -> None:
    transport = CommandTransport(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout_s=0.2,
    )
    with pytest.raises(ProtocolError) as exc_info:
        transport.complete("prompt")
    assert exc_info.value.code == "hermes_timeout"


def test_command_transport_missing_binary() -> None:
    transport = CommandTransport(["surface-hermes-does-not-exist-xyz"], timeout_s=5)
    with pytest.raises(ProtocolError) as exc_info:
        transport.complete("prompt")
    assert exc_info.value.code == "hermes_failed"
