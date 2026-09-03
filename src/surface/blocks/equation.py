from __future__ import annotations

from io import BytesIO

from matplotlib.mathtext import math_to_image
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from surface.blocks.base import Block
from surface.protocol import Command, EquationCommand


def latex_to_pixmap(latex: str, *, display: str) -> QPixmap:
    inner = f"\\displaystyle {latex}" if display == "block" else latex
    buf = BytesIO()
    try:
        math_to_image(f"${inner}$", buf, dpi=144, format="png")
    except (ValueError, RuntimeError):
        # mathtext has no \displaystyle; block still renders as $latex$.
        if display != "block":
            raise
        buf = BytesIO()
        math_to_image(f"${latex}$", buf, dpi=144, format="png")
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue())
    return pixmap


class EquationBlock(Block):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(command_id, parent)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        policy.setVerticalStretch(0)
        self.setSizePolicy(policy)

        self._source = QPixmap()
        self._label = QLabel(self)
        self._label.setSizePolicy(policy)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._label)

    def command_type(self) -> str:
        return "equation"

    def render(self, command: Command) -> None:
        if not isinstance(command, EquationCommand):
            self._source = QPixmap()
            self._label.setPixmap(QPixmap())
            self._label.setText("equation render failed: TypeError")
            return
        try:
            self._source = latex_to_pixmap(command.latex, display=command.display)
            self._label.setPixmap(self._fitted(self._source))
            self._label.setText("")
        except (ValueError, RuntimeError, Exception):
            self._source = QPixmap()
            self._label.setPixmap(QPixmap())
            self._label.setText(f"equation render failed: {command.latex}")

    def sizeHint(self) -> QSize:
        pixmap = self._label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            return QSize(pixmap.width(), pixmap.height())
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        pixmap = self._label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            return QSize(0, pixmap.height())
        return super().minimumSizeHint()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._source.isNull():
            return
        fitted = self._fitted(self._source)
        current = self._label.pixmap()
        if current is None or current.isNull() or current.size() != fitted.size():
            self._label.setPixmap(fitted)
            self.updateGeometry()

    def _fitted(self, pixmap: QPixmap) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        max_width = self._available_width()
        if max_width > 0 and pixmap.width() > max_width:
            return pixmap.scaled(
                max_width,
                pixmap.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        return pixmap

    def _available_width(self) -> int:
        parent = self.parentWidget()
        if parent is not None:
            margins = parent.contentsMargins()
            width = parent.width() - margins.left() - margins.right()
            if width > 0:
                return width
        return self.width()
