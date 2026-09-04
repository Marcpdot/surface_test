# Qt-free. Replaceable Hermes I/O. Surface never imports a model SDK.
from __future__ import annotations

import os
import shlex
import subprocess
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


class CommandTransport:
    """One subprocess per request. stdin=prompt, stdout=raw Hermes text."""

    def __init__(self, argv: list[str], *, timeout_s: float = 60.0) -> None:
        if not argv:
            raise ProtocolError("hermes_unavailable", "Hermes is not configured")
        self._argv = argv
        self._timeout_s = timeout_s

    def complete(self, prompt: str) -> str:
        try:
            completed = subprocess.run(
                self._argv,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProtocolError("hermes_timeout", "Hermes timed out") from exc
        except OSError as exc:
            raise ProtocolError(
                "hermes_failed", f"Hermes failed to start: {exc}"
            ) from exc
        if completed.returncode != 0:
            raise ProtocolError(
                "hermes_failed",
                f"Hermes exited {completed.returncode}",
            )
        return completed.stdout


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
