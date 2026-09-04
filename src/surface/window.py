import logging
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from surface.dispatcher import Dispatcher, DispatchResult
from surface.hermes_bridge import HermesBridge, is_structured_input
from surface.hermes_transport import HermesTransport, transport_from_env
from surface.protocol import Command, ProtocolError
from surface.study import StudyError, StudySession, StudyTurn
from surface.workspace import Workspace

_TITLE_BAR_HEIGHT = 32
_INPUT_HEIGHT = 72
_DEFAULT_SIZE = (960, 720)
_MIN_SIZE = (640, 480)


class _TitleBar(QWidget):
    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setFixedHeight(_TITLE_BAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(0)

        title = QLabel("Surface", self)
        layout.addWidget(title)
        layout.addStretch()

        minimize = QPushButton("_", self)
        minimize.setFixedSize(_TITLE_BAR_HEIGHT, _TITLE_BAR_HEIGHT)
        minimize.setFlat(True)
        minimize.setFocusPolicy(Qt.NoFocus)
        minimize.clicked.connect(host.showMinimized)
        layout.addWidget(minimize)

        close_btn = QPushButton("X", self)
        close_btn.setFixedSize(_TITLE_BAR_HEIGHT, _TITLE_BAR_HEIGHT)
        close_btn.setFlat(True)
        close_btn.setFocusPolicy(Qt.NoFocus)
        close_btn.clicked.connect(host.close)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            # Child widgets have no handle; drag the top-level window.
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)


class _InputEdit(QPlainTextEdit):
    submitted = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(_INPUT_HEIGHT)
        self.setPlaceholderText(
            "Natural language goes to Hermes. JSON still works. Ctrl+Enter sends."
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and (
            event.modifiers() & Qt.ControlModifier
        ):
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class _HermesThread(QThread):
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        bridge: HermesBridge,
        transport: HermesTransport,
        text: str,
        workspace_snapshot: dict[str, object],
        study_context: dict[str, object] | None,
    ) -> None:
        super().__init__()
        self._bridge = bridge
        self._transport = transport
        self._text = text
        self._workspace_snapshot = workspace_snapshot
        self._study_context = study_context

    def run(self) -> None:
        try:
            commands = self._bridge.complete(
                self._text,
                self._transport,
                self._workspace_snapshot,
                self._study_context,
            )
        except Exception as exc:
            self.failed.emit(exc)
            return
        self.succeeded.emit(commands)


class SurfaceWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Surface")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(*_DEFAULT_SIZE)
        self.setMinimumSize(*_MIN_SIZE)
        self.setStyleSheet("background-color: #F5F5F5;")
        self._centered = False

        self._workspace = Workspace(self)
        self._dispatcher = Dispatcher(self._workspace)
        self._bridge = HermesBridge()
        self._study = StudySession()
        self._transport = transport_from_env()
        self._busy = False
        self._hermes_thread: _HermesThread | None = None
        self._pending_study_turn: StudyTurn | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(_TitleBar(self))

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._workspace)
        root.addWidget(scroll, 1)

        self._status = QLabel(self)
        self._status.setTextFormat(Qt.PlainText)
        font = self._status.font()
        font.setPointSize(11)
        self._status.setFont(font)
        root.addWidget(self._status)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(8, 4, 8, 4)
        input_row.setSpacing(8)
        self._input = _InputEdit(self)
        self._input.submitted.connect(self._submit_from_input)
        input_row.addWidget(self._input, 1)
        self._send = QPushButton("Send", self)
        self._send.clicked.connect(self._submit_from_input)
        input_row.addWidget(self._send)
        root.addLayout(input_row)

        self._size_grip = QSizeGrip(self)

    def submit_text(self, text: str) -> None:
        if not text.strip() or self._busy:
            return
        if is_structured_input(text):
            try:
                commands = self._bridge.from_user_input(text)
                self.apply_commands(commands)
            except ProtocolError as exc:
                self._set_status_error(exc)
            except Exception as exc:
                self._set_internal_error(exc)
            return
        if self._transport is None:
            self._set_status_error(
                ProtocolError("hermes_unavailable", "Hermes is not configured")
            )
            return
        try:
            study_turn = self._study.prepare(text, self._workspace)
        except StudyError as exc:
            self._set_study_error(exc)
            return
        self._set_busy(True)
        self._status.setText("waiting…")
        snapshot = self._workspace.snapshot()
        self._pending_study_turn = study_turn
        thread = _HermesThread(
            self._bridge,
            self._transport,
            text.strip(),
            snapshot,
            study_turn.prompt_context if study_turn is not None else None,
        )
        thread.succeeded.connect(self._on_hermes_ok)
        thread.failed.connect(self._on_hermes_fail)
        thread.finished.connect(thread.deleteLater)
        self._hermes_thread = thread
        thread.start()

    def _submit_from_input(self) -> None:
        self.submit_text(self._input.toPlainText())

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._input.setEnabled(not busy)
        self._send.setEnabled(not busy)

    def _on_hermes_ok(self, commands: object) -> None:
        self._set_busy(False)
        self._hermes_thread = None
        if not isinstance(commands, list):
            self._pending_study_turn = None
            self._set_internal_error(TypeError("Hermes result is not a command list"))
            return
        study_turn = self._pending_study_turn
        self._pending_study_turn = None
        if study_turn is not None:
            try:
                commands = self._study.finalize(
                    study_turn, commands, self._workspace
                )
            except StudyError as exc:
                self._set_study_error(exc)
                return
            if self.apply_commands(commands):
                try:
                    self._study.commit(study_turn)
                except StudyError as exc:
                    self._set_internal_error(exc)
                    return
                self._input.clear()
            return
        self._input.clear()
        self.apply_commands(commands)

    def _on_hermes_fail(self, exc: object) -> None:
        self._set_busy(False)
        self._hermes_thread = None
        self._pending_study_turn = None
        if isinstance(exc, ProtocolError):
            self._set_status_error(exc)
        elif isinstance(exc, BaseException):
            self._set_internal_error(exc)
        else:
            self._set_internal_error(RuntimeError(str(exc)))

    def run_demo(self) -> None:
        try:
            path = self._write_demo_png()
            raw = self._bridge.demo_output(image_source=str(path))
            self.inject_hermes_output(raw)
        except Exception as exc:
            self._set_internal_error(exc)

    def inject_hermes_output(self, raw: str) -> None:
        try:
            commands = self._bridge.from_hermes_output(raw)
            self.apply_commands(commands)
        except ProtocolError as exc:
            self._set_status_error(exc)
        except Exception as exc:
            self._set_internal_error(exc)

    def _write_demo_png(self) -> Path:
        path = Path(tempfile.gettempdir()) / "surface-demo.png"
        image = QImage(64, 64, QImage.Format_RGB32)
        image.fill(0xFF4A90D9)
        if not image.save(str(path), "PNG"):
            raise OSError(f"could not write {path}")
        return path

    def apply_commands(self, commands: list[Command]) -> bool:
        try:
            results = self._dispatcher.dispatch_many(commands)
            self._set_status_from_results(results)
            return bool(results) and all(result.ok for result in results)
        except Exception as exc:
            self._set_internal_error(exc)
            return False

    def _set_status_error(self, exc: ProtocolError) -> None:
        self._status.setText(f"{exc.code}: {exc.message}")
        logging.getLogger("surface").warning("%s %s", exc.code, exc.command_id)

    def _set_study_error(self, exc: StudyError) -> None:
        self._status.setText(f"{exc.code}: {exc.message}")
        logging.getLogger("surface.study").warning("%s", exc.code)

    def _set_internal_error(self, exc: BaseException) -> None:
        logging.getLogger("surface").exception("internal_error")
        self._status.setText(f"internal_error: {type(exc).__name__}")

    def _set_status_from_results(self, results: list[DispatchResult]) -> None:
        if not results:
            return
        first_err = next((r for r in results if not r.ok), None)
        if first_err is not None:
            self._status.setText(f"{first_err.error_code}: {first_err.error_message}")
            return
        if len(results) == 1:
            r = results[0]
            self._status.setText(f"{r.action} {r.command_id} ({r.command_type})")
            return
        self._status.setText(f"{len(results)} ok")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._centered:
            self._center_on_screen()
            self._centered = True
        self._position_size_grip()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_size_grip()

    def _center_on_screen(self) -> None:
        screen = self.screen()
        if screen is None:
            return
        frame = self.frameGeometry()
        frame.moveCenter(screen.availableGeometry().center())
        self.move(frame.topLeft())

    def _position_size_grip(self) -> None:
        grip = self._size_grip
        hint = grip.sizeHint()
        grip.setGeometry(
            self.width() - hint.width(),
            self.height() - hint.height(),
            hint.width(),
            hint.height(),
        )
        grip.raise_()
