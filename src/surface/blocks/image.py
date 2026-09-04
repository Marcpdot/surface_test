from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from surface.blocks.base import Block
from surface.image_source import resolve_image_file
from surface.protocol import Command, ImageCommand, ProtocolError

_MAX_HEIGHT = 480


class ImageBlock(Block):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(command_id, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._source_pixmap = QPixmap()

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.PlainText)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._label)

    def command_type(self) -> str:
        return "image"

    def render(self, command: Command) -> None:
        if not isinstance(command, ImageCommand):
            self._show_fallback("", "image render failed: TypeError")
            return
        try:
            path = resolve_image_file(command.source)
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                self._show_fallback(command.alt, "unreadable image")
                return
            self._source_pixmap = pixmap
            self._label.setPixmap(self._scaled(pixmap))
            self._label.setText("")
            self.updateGeometry()
        except ProtocolError as exc:
            self._show_fallback(command.alt, f"{exc.code}: {exc.message}")
        except Exception as exc:
            self._show_fallback(command.alt, f"image render failed: {type(exc).__name__}")

    def sizeHint(self) -> QSize:
        pixmap = self._label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            return QSize(super().sizeHint().width(), pixmap.height())
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        pixmap = self._label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            return QSize(super().minimumSizeHint().width(), pixmap.height())
        return super().minimumSizeHint()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._source_pixmap.isNull():
            return
        fitted = self._scaled(self._source_pixmap)
        current = self._label.pixmap()
        if current is None or current.isNull() or current.size() != fitted.size():
            self._label.setPixmap(fitted)
            self.updateGeometry()

    def _scaled(self, pixmap: QPixmap) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        max_width = self.width()
        if max_width <= 0:
            max_width = pixmap.width()
        if pixmap.width() <= max_width and pixmap.height() <= _MAX_HEIGHT:
            return pixmap
        return pixmap.scaled(
            max(1, max_width),
            _MAX_HEIGHT,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

    def _show_fallback(self, alt: str, error: str) -> None:
        text = alt.strip() or "(image)"
        self._source_pixmap = QPixmap()
        self._label.setPixmap(QPixmap())
        self._label.setText(f"{text}\n{error}")
        self.updateGeometry()
