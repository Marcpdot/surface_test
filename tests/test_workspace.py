from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from surface.blocks.layout import LayoutBlock
from surface.composition import CompositionError
from surface.protocol import (
    EquationCommand,
    LayoutCommand,
    MoveCommand,
    RemoveCommand,
    TextCommand,
)
from surface.workspace import Workspace


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _ids(layout: LayoutBlock) -> list[str]:
    return [
        layout._inner.itemAt(i).widget().command_id  # type: ignore[union-attr]
        for i in range(layout._inner.count())
    ]


def test_reconcile_moves_reorders_updates_and_removes_without_recreation(
    app: QApplication,
) -> None:
    workspace = Workspace()
    workspace.apply_many(
        [
            TextCommand(type="text", id="a", content="old"),
            TextCommand(type="text", id="b", content="b"),
            LayoutCommand(
                type="layout", id="row", direction="horizontal", children=("a", "b")
            ),
        ]
    )
    a_widget = workspace._blocks["a"]
    b_widget = workspace._blocks["b"]
    row_widget = workspace._blocks["row"]
    assert isinstance(row_widget, LayoutBlock)

    workspace.apply_many([MoveCommand(type="move", id="a", parent="row", index=1)])
    assert _ids(row_widget) == ["b", "a"]
    assert workspace._blocks["a"] is a_widget
    assert workspace._blocks["b"] is b_widget

    workspace.apply_many([TextCommand(type="text", id="a", content="new")])
    assert workspace._blocks["a"] is a_widget
    assert workspace.get("a").content == "new"  # type: ignore[union-attr]
    assert a_widget.parentWidget() is row_widget

    workspace.apply_many([MoveCommand(type="move", id="a", parent=None)])
    assert a_widget.parentWidget() is workspace
    assert _ids(row_widget) == ["b"]

    workspace.apply_many([RemoveCommand(type="remove", id="row")])
    assert "row" not in workspace.list_ids()
    assert b_widget.parentWidget() is workspace
    assert workspace.snapshot()["nodes"] == [
        {"id": "a", "type": "text", "parent": None, "index": 0},
        {"id": "b", "type": "text", "parent": None, "index": 1},
    ]
    workspace.deleteLater()
    app.processEvents()


def test_invalid_batch_leaves_widgets_and_snapshot_unchanged(app: QApplication) -> None:
    workspace = Workspace()
    workspace.apply_many([TextCommand(type="text", id="a", content="old")])
    widget = workspace._blocks["a"]
    before = workspace.snapshot()

    with pytest.raises(CompositionError):
        workspace.apply_many(
            [
                TextCommand(type="text", id="a", content="new"),
                MoveCommand(type="move", id="missing", parent=None),
            ]
        )

    assert workspace.snapshot() == before
    assert workspace.get("a").content == "old"  # type: ignore[union-attr]
    assert workspace._blocks["a"] is widget
    workspace.deleteLater()
    app.processEvents()


def test_remove_then_recreate_id_with_new_type_replaces_widget(app: QApplication) -> None:
    workspace = Workspace()
    workspace.apply_many([TextCommand(type="text", id="node", content="old")])
    old_widget = workspace._blocks["node"]
    workspace.apply_many(
        [
            RemoveCommand(type="remove", id="node"),
            EquationCommand(type="equation", id="node", latex="x = 1"),
        ]
    )
    assert workspace._blocks["node"] is not old_widget
    assert workspace.get("node").type == "equation"  # type: ignore[union-attr]
    workspace.deleteLater()
    app.processEvents()
