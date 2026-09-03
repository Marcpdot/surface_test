from __future__ import annotations

from math import ceil

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QResizeEvent, QTextDocument
from PySide6.QtWidgets import QSizePolicy, QTextBrowser, QVBoxLayout, QWidget

from surface.blocks.base import Block
from surface.protocol import Command, TextCommand


class TextBlock(Block):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(command_id, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._browser = QTextBrowser(self)
        self._browser.setReadOnly(True)
        self._browser.setOpenLinks(False)
        self._browser.setOpenExternalLinks(False)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._browser.document().documentLayout().documentSizeChanged.connect(
            self._on_document_size_changed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._browser)

    def command_type(self) -> str:
        return "text"

    def render(self, command: Command) -> None:
        if not isinstance(command, TextCommand):
            self._set_plain("(text render failed)")
            return
        try:
            if command.format == "plain":
                self._browser.setPlainText(command.content)
            else:
                self._browser.document().setMarkdown(
                    command.content,
                    QTextDocument.MarkdownFeature.MarkdownDialectGitHub
                    | QTextDocument.MarkdownFeature.MarkdownNoHTML,
                )
        except Exception:
            try:
                self._browser.setPlainText(command.content)
            except Exception:
                self._set_plain("(text render failed)")

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self._document_height())

    def minimumSizeHint(self) -> QSize:
        return QSize(super().minimumSizeHint().width(), self._document_height())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._sync_document_width()

    def _on_document_size_changed(self, _size: object = None) -> None:
        self.updateGeometry()

    def _sync_document_width(self) -> None:
        width = self._browser.viewport().width()
        if width > 0:
            self._browser.document().setTextWidth(width)

    def _document_height(self) -> int:
        height = ceil(self._browser.document().size().height())
        frame = self._browser.frameWidth() * 2
        margins = self._browser.contentsMargins()
        return height + frame + margins.top() + margins.bottom()

    def _set_plain(self, text: str) -> None:
        try:
            self._browser.setPlainText(text)
        except Exception:
            pass
