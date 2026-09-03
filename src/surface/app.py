def run(argv: list[str] | None = None) -> int:
    """Temporary scaffold until PR 2 opens the Qt window."""
    import sys
    sys.stderr.write("surface v0.1 scaffold\n")
    return 0


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(run(argv))
