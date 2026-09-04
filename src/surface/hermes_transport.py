# Qt-free. Replaceable Hermes I/O. Surface never imports a model SDK.
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Mapping, Protocol as TypingProtocol

from surface.protocol import ProtocolError


class HermesTransport(TypingProtocol):
    def complete(self, prompt: str) -> str: ...


class FakeTransport:
    def __init__(
        self,
        output: str = "",
        error: ProtocolError | None = None,
    ) -> None:
        self.output = output
        self.error = error
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return self.output


def _decode_utf8(data: bytes | None) -> str:
    return (data or b"").decode("utf-8")


def _oneshot_argv(argv: list[str], prompt: str) -> list[str]:
    """Build argv for a non-interactive one-shot. Never launches `hermes` REPL.

    Hermes scripted mode is ``hermes -z PROMPT`` (prompt is an argument, not
    stdin). A bare ``hermes`` token gets ``-z`` inserted.
    """
    out = list(argv)
    if not out:
        raise ProtocolError("hermes_unavailable", "Hermes is not configured")
    stem = Path(out[0]).stem.lower()
    if stem in {"hermes", "hermes.cmd"} and "-z" not in out and "--oneshot" not in out:
        out.append("-z")
    out.append(prompt)
    return out


class CommandTransport:
    """One subprocess per request. Prompt is the last argv token (Hermes ``-z``)."""

    def __init__(self, argv: list[str], *, timeout_s: float = 60.0) -> None:
        if not argv:
            raise ProtocolError("hermes_unavailable", "Hermes is not configured")
        self._argv = argv
        self._timeout_s = timeout_s

    def complete(self, prompt: str) -> str:
        argv = _oneshot_argv(self._argv, prompt)
        try:
            completed = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProtocolError("hermes_timeout", "Hermes timed out") from exc
        except OSError as exc:
            raise ProtocolError(
                "hermes_failed", f"Hermes failed to start: {exc}"
            ) from exc
        stdout = _decode_utf8(completed.stdout)
        if completed.returncode != 0:
            raise ProtocolError(
                "hermes_failed",
                f"Hermes exited {completed.returncode}",
            )
        return stdout


def transport_from_env(
    env: Mapping[str, str] | None = None,
) -> CommandTransport | None:
    env = os.environ if env is None else env
    cmd = (env.get("SURFACE_HERMES_CMD") or "").strip()
    if not cmd:
        return None
    raw_timeout = (env.get("SURFACE_HERMES_TIMEOUT_S") or "60").strip()
    try:
        timeout_s = float(raw_timeout)
    except ValueError:
        timeout_s = 60.0
    if timeout_s <= 0:
        timeout_s = 60.0
    argv = shlex.split(cmd, posix=(os.name != "nt"))
    if not argv:
        return None
    return CommandTransport(argv, timeout_s=timeout_s)
