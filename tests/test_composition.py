import pytest

from surface.composition import CompositionError, apply_layout_parents


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
