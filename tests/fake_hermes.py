"""Stub process for CommandTransport tests. Not a model.

Mimics ``hermes -z PROMPT``: prompt is the last argv token, stdin unused.
"""

from __future__ import annotations

import json
import sys

_BODY = '{"type":"text","id":"stub-1","content":"stub"}'
_UTF8_BODY = json.dumps(
    {"type": "text", "id": "stub-1", "content": "σ bøye 日本語"},
    ensure_ascii=False,
)


def main(argv: list[str]) -> int:
    if "--fail" in argv:
        sys.stderr.buffer.write("stub fail\n".encode("utf-8"))
        return 2
    if "--empty" in argv:
        return 0
    if "--utf8" in argv:
        sys.stdout.buffer.write(_UTF8_BODY.encode("utf-8") + b"\n")
        return 0
    if "--echo-prompt" in argv:
        prompt = argv[-1] if argv else ""
        sys.stdout.buffer.write(
            json.dumps(
                {"type": "text", "id": "stub-1", "content": prompt},
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        return 0
    if "--fence" in argv:
        sys.stdout.buffer.write(("```json\n" + _BODY + "\n```\n").encode("utf-8"))
        return 0
    sys.stdout.buffer.write((_BODY + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
