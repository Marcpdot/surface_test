from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from surface.blocks import create_block
from surface.blocks.base import Block
from surface.dispatcher import TypeMismatchError
from surface.protocol import Command


class Workspace(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._blocks: dict[str, Block] = {}
        self._commands: dict[str, Command] = {}

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addStretch()

    def upsert(self, command: Command) -> Literal["created", "updated"]:
        existing = self._blocks.get(command.id)
        if existing is None:
            block = create_block(command, parent=self)  # UnknownBlockError før mutasjon
            block.render(command)  # kaster aldri; kan vise fallback
            # Stretch stays last so blocks pack to the top.
            self._layout.insertWidget(self._layout.count() - 1, block)
            self._blocks[command.id] = block
            self._commands[command.id] = command
            return "created"
        if existing.command_type() != command.type:
            raise TypeMismatchError(command.id, existing.command_type(), command.type)
        existing.render(command)  # kaster aldri
        self._commands[command.id] = command
        return "updated"

    def get(self, command_id: str) -> Command | None:
        return self._commands.get(command_id)

    def remove(self, command_id: str) -> bool:
        block = self._blocks.pop(command_id, None)
        if block is None:
            return False
        self._commands.pop(command_id, None)
        self._layout.removeWidget(block)
        block.setParent(None)
        block.deleteLater()
        return True

    def list_ids(self) -> list[str]:
        return list(self._commands)

    def sizeHint(self) -> QSize:
        return self._layout.sizeHint()
