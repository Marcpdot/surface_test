def run(argv: list[str] | None = None) -> int:
    """Packaging smoke-check; does not start a GUI."""
    import sys
    sys.stderr.write("surface v0.1 scaffold\n")
    return 0


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(run(argv))
