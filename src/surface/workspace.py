from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from surface.blocks import create_block
from surface.blocks.base import Block
from surface.blocks.layout import LayoutBlock
from surface.composition import PlannedAction, WorkspaceState, plan_batch
from surface.protocol import Command, LayoutCommand, NodeCommand


class Workspace(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._blocks: dict[str, Block] = {}
        self._state = WorkspaceState.empty()

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addStretch()

    def apply_many(self, commands: list[Command]) -> list[PlannedAction]:
        plan = plan_batch(self._state, commands)
        self._reconcile(plan.state, plan.render_ids, plan.removed_ids)
        self._state = plan.state
        return list(plan.actions)

    def upsert(self, command: NodeCommand) -> Literal["created", "updated"]:
        """Compatibility one-node API; dispatcher uses atomic ``apply_many``."""
        action = self.apply_many([command])[0].action
        assert action in ("created", "updated")
        return action

    def _reconcile(
        self,
        next_state: WorkspaceState,
        render_ids: frozenset[str],
        removed_ids: frozenset[str],
    ) -> None:
        next_blocks = dict(self._blocks)
        prepared: dict[str, Block] = {}

        for node_id in next_state.commands:
            if node_id not in next_blocks or node_id in removed_ids:
                command = next_state.commands[node_id]
                block = create_block(command, parent=self)
                block.render(command)
                prepared[node_id] = block

        for node_id in render_ids:
            if (
                node_id in self._blocks
                and node_id not in removed_ids
                and node_id in next_state.commands
            ):
                next_blocks[node_id].render(next_state.commands[node_id])

        for block in self._blocks.values():
            if isinstance(block, LayoutBlock):
                block.set_children([])

        for block in next_blocks.values():
            self._layout.removeWidget(block)

        for node_id in removed_ids:
            block = next_blocks.pop(node_id)
            block.setParent(None)
            block.deleteLater()

        next_blocks.update(prepared)

        for node_id, command in next_state.commands.items():
            if not isinstance(command, LayoutCommand):
                continue
            layout_block = next_blocks[node_id]
            assert isinstance(layout_block, LayoutBlock)
            layout_block.set_children([next_blocks[child] for child in command.children])

        for node_id in next_state.root_children:
            self._layout.insertWidget(self._layout.count() - 1, next_blocks[node_id])

        self._blocks = next_blocks

    def get(self, command_id: str) -> NodeCommand | None:
        return self._state.commands.get(command_id)

    def list_ids(self) -> list[str]:
        return list(self._state.commands)

    def snapshot(self) -> dict[str, object]:
        return self._state.snapshot()

    def sizeHint(self) -> QSize:
        return self._layout.sizeHint()
