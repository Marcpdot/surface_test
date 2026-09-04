"""Stub process for CommandTransport tests. Not a model."""

from __future__ import annotations

import sys

_BODY = '{"type":"text","id":"stub-1","content":"stub"}'


def main(argv: list[str]) -> int:
    sys.stdin.read()
    if "--fail" in argv:
        sys.stderr.write("stub fail\n")
        return 2
    if "--empty" in argv:
        return 0
    if "--fence" in argv:
        sys.stdout.write("```json\n" + _BODY + "\n```\n")
        return 0
    sys.stdout.write(_BODY + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
