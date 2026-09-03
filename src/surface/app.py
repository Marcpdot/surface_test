import argparse
import logging
import sys


def run(argv: list[str] | None = None) -> int:
    """CLI + event loop. argv is arguments without the program name (sys.argv[1:]).

    Return codes:
        0 — event loop ended normally (window closed).
        2 — CLI usage error. Written to stderr. No QApplication.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="surface", exit_on_error=False)
    parser.add_argument("--demo", action="store_true")
    try:
        args = parser.parse_args(argv)
    except argparse.ArgumentError as exc:
        parser.print_usage(sys.stderr)
        sys.stderr.write(f"{parser.prog}: error: {exc}\n")
        return 2
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 2

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
    return app.exec()


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(run(argv))
