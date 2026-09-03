from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

_TITLE_BAR_HEIGHT = 32
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


class SurfaceWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Surface")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(*_DEFAULT_SIZE)
        self.setMinimumSize(*_MIN_SIZE)
        self.setStyleSheet("background-color: #F5F5F5;")
        self._centered = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(_TitleBar(self))
        root.addWidget(QWidget(self), 1)

        self._size_grip = QSizeGrip(self)

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
