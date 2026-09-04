# Qt-free v0.2 apply checks: unknown child, already composed, cycle.
from __future__ import annotations

_SAFETY_HOPS = 8


class CompositionError(Exception):
    def __init__(self, code: str, message: str, *, command_id: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.command_id = command_id


def apply_layout_parents(
    layout_id: str,
    children: tuple[str, ...],
    *,
    known_ids: frozenset[str],
    parent_of: dict[str, str | None],
) -> dict[str, str | None]:
    """Return a new parent map for this layout upsert.

    ``known_ids`` is the workspace before inserting a new layout id.
    Children already parented to ``layout_id`` may stay. Other parents reject.
    Dropped children (parent was this layout, not in ``children``) go to root.
    """
    for child in children:
        if child not in known_ids:
            raise CompositionError(
                "unknown_child",
                f"unknown child {child!r}",
                command_id=layout_id,
            )
        current_parent = parent_of.get(child)
        if current_parent is not None and current_parent != layout_id:
            raise CompositionError(
                "already_composed",
                f"child {child!r} already in {current_parent!r}",
                command_id=layout_id,
            )
        _reject_cycle(layout_id, child, parent_of)

    next_parents = dict(parent_of)
    for existing, parent in list(next_parents.items()):
        if parent == layout_id and existing not in children:
            next_parents[existing] = None
    for child in children:
        next_parents[child] = layout_id
    return next_parents


def _reject_cycle(
    layout_id: str,
    child: str,
    parent_of: dict[str, str | None],
) -> None:
    if child == layout_id:
        raise CompositionError(
            "cycle",
            f"layout {layout_id!r} cannot contain itself",
            command_id=layout_id,
        )
    current: str | None = layout_id
    hops = 0
    while current is not None:
        if current == child:
            raise CompositionError(
                "cycle",
                f"child {child!r} is an ancestor of {layout_id!r}",
                command_id=layout_id,
            )
        hops += 1
        if hops > _SAFETY_HOPS:
            raise CompositionError(
                "limit_exceeded",
                "layout ancestry exceeds safety limit",
                command_id=layout_id,
            )
        current = parent_of.get(current)
