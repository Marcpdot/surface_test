import pytest

from surface.composition import (
    CompositionError,
    WorkspaceState,
    apply_layout_parents,
    plan_batch,
)
from surface.protocol import LayoutCommand, MoveCommand, RemoveCommand, TextCommand


def _apply(
    layout_id: str,
    children: tuple[str, ...],
    *,
    known: set[str],
    parents: dict[str, str | None],
) -> dict[str, str | None]:
    return apply_layout_parents(
        layout_id,
        children,
        known_ids=frozenset(known),
        parent_of=parents,
    )


def test_horizontal_row_assigns_parents() -> None:
    known = {"problem-1", "figure-1"}
    parents: dict[str, str | None] = {}
    next_map = _apply(
        "row-problem", ("problem-1", "figure-1"), known=known, parents=parents
    )
    assert next_map["problem-1"] == "row-problem"
    assert next_map["figure-1"] == "row-problem"
    assert parents == {}


def test_nested_layouts() -> None:
    known = {
        "problem-1",
        "figure-1",
        "row-problem",
        "row-model",
        "equation-1",
        "plot-1",
    }
    parents = {
        "problem-1": "row-problem",
        "figure-1": "row-problem",
        "equation-1": "row-model",
        "plot-1": "row-model",
    }
    next_map = _apply(
        "study-1",
        ("row-problem", "row-model"),
        known=known,
        parents=parents,
    )
    assert next_map["row-problem"] == "study-1"
    assert next_map["row-model"] == "study-1"
    assert next_map["problem-1"] == "row-problem"


def test_unknown_child() -> None:
    with pytest.raises(CompositionError) as exc_info:
        _apply("row-1", ("missing-1",), known=set(), parents={})
    assert exc_info.value.code == "unknown_child"


def test_already_composed() -> None:
    parents = {"figure-1": "other-row"}
    with pytest.raises(CompositionError) as exc_info:
        _apply(
            "row-problem",
            ("figure-1",),
            known={"figure-1"},
            parents=parents,
        )
    assert exc_info.value.code == "already_composed"


def test_update_drops_child_to_root() -> None:
    parents = {"problem-1": "row-problem", "figure-1": "row-problem"}
    next_map = _apply(
        "row-problem",
        ("problem-1",),
        known={"problem-1", "figure-1", "row-problem"},
        parents=parents,
    )
    assert next_map["problem-1"] == "row-problem"
    assert next_map["figure-1"] is None


def test_self_cycle() -> None:
    with pytest.raises(CompositionError) as exc_info:
        _apply("row-1", ("row-1",), known={"row-1"}, parents={})
    assert exc_info.value.code == "cycle"


def test_ancestor_cycle() -> None:
    parents = {"row-1": "study-1"}
    with pytest.raises(CompositionError) as exc_info:
        _apply(
            "row-1",
            ("study-1",),
            known={"row-1", "study-1"},
            parents=parents,
        )
    assert exc_info.value.code == "cycle"


def _state(*commands):
    return plan_batch(WorkspaceState.empty(), list(commands)).state


def test_move_reparents_and_reorders() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        TextCommand(type="text", id="b", content="b"),
        LayoutCommand(type="layout", id="row", direction="horizontal", children=("a", "b")),
    )
    moved = plan_batch(
        state, [MoveCommand(type="move", id="a", parent="row", index=1)]
    )
    assert moved.actions[0].action == "moved"
    assert moved.state.commands["row"].children == ("b", "a")


def test_move_to_root_and_into_other_layout() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        TextCommand(type="text", id="b", content="b"),
        LayoutCommand(type="layout", id="left", direction="vertical", children=("a",)),
        LayoutCommand(type="layout", id="right", direction="vertical", children=("b",)),
    )
    at_root = plan_batch(state, [MoveCommand(type="move", id="a", parent=None)]).state
    assert at_root.parent_of["a"] is None
    assert at_root.root_children[-1] == "a"
    moved = plan_batch(
        at_root, [MoveCommand(type="move", id="a", parent="right", index=0)]
    ).state
    assert moved.commands["right"].children == ("a", "b")
    assert moved.commands["left"].children == ()


def test_move_rejects_unknown_parent_non_layout_and_bad_index() -> None:
    state = _state(TextCommand(type="text", id="a", content="a"))
    for command, code in [
        (MoveCommand(type="move", id="missing", parent=None), "unknown_id"),
        (MoveCommand(type="move", id="a", parent="missing"), "invalid_parent"),
        (MoveCommand(type="move", id="a", parent="a"), "invalid_parent"),
        (MoveCommand(type="move", id="a", parent=None, index=2), "invalid_index"),
    ]:
        with pytest.raises(CompositionError) as exc_info:
            plan_batch(state, [command])
        assert exc_info.value.code == code


def test_move_rejects_descendant_cycle() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        LayoutCommand(type="layout", id="inner", direction="vertical", children=("a",)),
        LayoutCommand(type="layout", id="outer", direction="vertical", children=("inner",)),
    )
    with pytest.raises(CompositionError) as exc_info:
        plan_batch(state, [MoveCommand(type="move", id="outer", parent="inner")])
    assert exc_info.value.code == "cycle"


def test_remove_primitive_and_layout_promotes_direct_children_to_root() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        TextCommand(type="text", id="b", content="b"),
        LayoutCommand(type="layout", id="row", direction="horizontal", children=("a", "b")),
    )
    without_a = plan_batch(state, [RemoveCommand(type="remove", id="a")]).state
    assert "a" not in without_a.commands
    assert without_a.commands["row"].children == ("b",)

    without_row = plan_batch(state, [RemoveCommand(type="remove", id="row")]).state
    assert "row" not in without_row.commands
    assert without_row.root_children == ("a", "b")
    assert without_row.parent_of == {"a": None, "b": None}


def test_primitive_upsert_preserves_placement() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="old"),
        LayoutCommand(type="layout", id="row", direction="vertical", children=("a",)),
    )
    updated = plan_batch(
        state, [TextCommand(type="text", id="a", content="new")]
    ).state
    assert updated.parent_of["a"] == "row"
    assert updated.commands["row"].children == ("a",)
    assert updated.commands["a"].content == "new"


def test_invalid_late_command_does_not_change_input_state() -> None:
    state = _state(TextCommand(type="text", id="a", content="old"))
    before = state.snapshot()
    with pytest.raises(CompositionError):
        plan_batch(
            state,
            [
                TextCommand(type="text", id="a", content="new"),
                MoveCommand(type="move", id="missing", parent=None),
            ],
        )
    assert state.snapshot() == before
    assert state.commands["a"].content == "old"


def test_snapshot_has_semantic_order_without_content() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="secret"),
        LayoutCommand(type="layout", id="row", direction="horizontal", children=("a",)),
    )
    assert state.snapshot() == {
        "nodes": [
            {"id": "a", "type": "text", "parent": "row", "index": 0},
            {
                "id": "row",
                "type": "layout",
                "parent": None,
                "index": 0,
                "direction": "horizontal",
            },
        ]
    }


def test_move_uses_explicit_root_index() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        TextCommand(type="text", id="b", content="b"),
    )
    moved = plan_batch(
        state, [MoveCommand(type="move", id="b", parent=None, index=0)]
    ).state
    assert moved.root_children == ("b", "a")


def test_move_rejects_layout_capacity_overflow() -> None:
    children = tuple(f"a-{index}" for index in range(8))
    commands = [TextCommand(type="text", id=node_id, content=node_id) for node_id in children]
    commands.extend(
        [
            TextCommand(type="text", id="extra", content="extra"),
            LayoutCommand(
                type="layout", id="full", direction="vertical", children=children
            ),
        ]
    )
    state = _state(*commands)
    with pytest.raises(CompositionError) as exc_info:
        plan_batch(state, [MoveCommand(type="move", id="extra", parent="full")])
    assert exc_info.value.code == "limit_exceeded"


def test_remove_nested_layout_keeps_descendants_together() -> None:
    state = _state(
        TextCommand(type="text", id="a", content="a"),
        LayoutCommand(type="layout", id="inner", direction="vertical", children=("a",)),
        LayoutCommand(type="layout", id="outer", direction="vertical", children=("inner",)),
    )
    removed = plan_batch(
        state, [RemoveCommand(type="remove", id="outer")]
    ).state
    assert removed.root_children == ("inner",)
    assert removed.parent_of["inner"] is None
    assert removed.parent_of["a"] == "inner"
    assert removed.commands["inner"].children == ("a",)
