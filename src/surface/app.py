import argparse
import logging
import sys
from pathlib import Path


def run(argv: list[str] | None = None) -> int:
    """CLI + event loop. argv is arguments without the program name (sys.argv[1:]).

    Return codes:
        0 — event loop ended normally (window closed).
        2 — CLI usage error: unknown/extra positional args, both --demo and --inject,
            missing PATH for --inject, --inject file missing / not a file / unreadable.
            Written to stderr. No QApplication, no window.
        1 — unexpected error before the event loop (logged).
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="surface",
        exit_on_error=False,
        epilog=(
            "Natural language uses Hermes: set SURFACE_HERMES_CMD "
            "(argv, stdin=prompt, stdout=JSON). Optional SURFACE_HERMES_TIMEOUT_S "
            "(default 60). JSON paste, --inject, and --demo do not call Hermes."
        ),
    )
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument("--demo", action="store_true")
    exclusive.add_argument("--inject", metavar="PATH")
    try:
        args = parser.parse_args(argv)
    except argparse.ArgumentError as exc:
        parser.print_usage(sys.stderr)
        sys.stderr.write(f"{parser.prog}: error: {exc}\n")
        return 2
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 2

    inject_text: str | None = None
    if args.inject is not None:
        path = Path(args.inject)
        try:
            if not path.exists():
                sys.stderr.write(
                    f"{parser.prog}: error: --inject file not found: {path}\n"
                )
                return 2
            if not path.is_file():
                sys.stderr.write(
                    f"{parser.prog}: error: --inject path is not a file: {path}\n"
                )
                return 2
            inject_text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            sys.stderr.write(
                f"{parser.prog}: error: cannot read --inject file: {exc}\n"
            )
            return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    import os
    os.environ.setdefault("QT_API", "PySide6")
    import matplotlib
    matplotlib.use("QtAgg")
    from PySide6.QtWidgets import QApplication
    from surface.window import SurfaceWindow

    app = QApplication(sys.argv)
    win = SurfaceWindow()
    win.show()
    if args.demo:
        win.run_demo()
    elif inject_text is not None:
        win.inject_hermes_output(inject_text)
    return app.exec()


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(run(argv))
