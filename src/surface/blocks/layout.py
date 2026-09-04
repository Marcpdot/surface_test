from __future__ import annotations

from PySide6.QtWidgets import QBoxLayout, QSizePolicy, QWidget

from surface.blocks.base import Block
from surface.protocol import Command, LayoutCommand


class LayoutBlock(Block):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(command_id, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._inner = QBoxLayout(QBoxLayout.TopToBottom, self)
        self._inner.setContentsMargins(0, 0, 0, 0)
        self._inner.setSpacing(12)

    def command_type(self) -> str:
        return "layout"

    def render(self, command: Command) -> None:
        try:
            if not isinstance(command, LayoutCommand):
                return
            if command.direction == "horizontal":
                self._inner.setDirection(QBoxLayout.LeftToRight)
            else:
                self._inner.setDirection(QBoxLayout.TopToBottom)
        except Exception:
            return

    def set_children(self, widgets: list[QWidget]) -> None:
        while self._inner.count():
            item = self._inner.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        for widget in widgets:
            self._inner.addWidget(widget, 1)
