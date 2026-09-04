from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from surface.blocks import create_block
from surface.blocks.base import Block
from surface.blocks.layout import LayoutBlock
from surface.composition import apply_layout_parents
from surface.dispatcher import TypeMismatchError
from surface.protocol import Command, LayoutCommand


class Workspace(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._blocks: dict[str, Block] = {}
        self._commands: dict[str, Command] = {}
        self._parent_of: dict[str, str | None] = {}

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addStretch()

    def upsert(self, command: Command) -> Literal["created", "updated"]:
        if isinstance(command, LayoutCommand):
            return self._upsert_layout(command)
        existing = self._blocks.get(command.id)
        if existing is None:
            block = create_block(command, parent=self)
            block.render(command)
            self._layout.insertWidget(self._layout.count() - 1, block)
            self._blocks[command.id] = block
            self._commands[command.id] = command
            self._parent_of[command.id] = None
            return "created"
        if existing.command_type() != command.type:
            raise TypeMismatchError(command.id, existing.command_type(), command.type)
        existing.render(command)
        self._commands[command.id] = command
        return "updated"

    def _upsert_layout(self, command: LayoutCommand) -> Literal["created", "updated"]:
        existing = self._blocks.get(command.id)
        if existing is not None and existing.command_type() != "layout":
            raise TypeMismatchError(command.id, existing.command_type(), command.type)
        next_parents = apply_layout_parents(
            command.id,
            command.children,
            known_ids=frozenset(self._commands),
            parent_of=self._parent_of,
        )
        dropped = [
            child_id
            for child_id, parent in self._parent_of.items()
            if parent == command.id and child_id not in command.children
        ]
        if existing is None:
            block = create_block(command, parent=self)
            block.render(command)
            self._layout.insertWidget(self._layout.count() - 1, block)
            self._blocks[command.id] = block
            self._commands[command.id] = command
            self._parent_of = next_parents
            self._parent_of.setdefault(command.id, None)
            action: Literal["created", "updated"] = "created"
        else:
            existing.render(command)
            self._commands[command.id] = command
            self._parent_of = next_parents
            action = "updated"

        layout_block = self._blocks[command.id]
        assert isinstance(layout_block, LayoutBlock)
        for child_id in command.children:
            child = self._blocks[child_id]
            self._layout.removeWidget(child)
        layout_block.set_children([self._blocks[child_id] for child_id in command.children])
        for child_id in dropped:
            self._place_on_root(self._blocks[child_id])
        return action

    def _place_on_root(self, block: Block) -> None:
        self._layout.insertWidget(self._layout.count() - 1, block)

    def get(self, command_id: str) -> Command | None:
        return self._commands.get(command_id)

    def list_ids(self) -> list[str]:
        return list(self._commands)

    def sizeHint(self) -> QSize:
        return self._layout.sizeHint()
