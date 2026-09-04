# Qt-free workspace ownership, ordering, and batch validation.
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from surface.protocol import (
    MAX_CHILDREN,
    Command,
    LayoutCommand,
    MoveCommand,
    NodeCommand,
    RemoveCommand,
)

_SAFETY_HOPS = 8
WorkspaceAction = Literal["created", "updated", "moved", "removed"]


class CompositionError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        command_id: str,
        command_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.command_id = command_id
        self.command_type = command_type


@dataclass(frozen=True)
class WorkspaceState:
    commands: dict[str, NodeCommand]
    parent_of: dict[str, str | None]
    root_children: tuple[str, ...]

    @classmethod
    def empty(cls) -> WorkspaceState:
        return cls(commands={}, parent_of={}, root_children=())

    def snapshot(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        for node_id, command in self.commands.items():
            parent = self.parent_of[node_id]
            siblings = self.root_children if parent is None else _layout(self, parent).children
            node: dict[str, object] = {
                "id": node_id,
                "type": command.type,
                "parent": parent,
                "index": siblings.index(node_id),
            }
            if isinstance(command, LayoutCommand):
                node["direction"] = command.direction
            nodes.append(node)
        return {"nodes": nodes}


@dataclass(frozen=True)
class PlannedAction:
    command_id: str
    command_type: str
    action: WorkspaceAction


@dataclass(frozen=True)
class BatchPlan:
    state: WorkspaceState
    actions: tuple[PlannedAction, ...]
    render_ids: frozenset[str]
    removed_ids: frozenset[str]


def plan_batch(current: WorkspaceState, commands: list[Command]) -> BatchPlan:
    """Validate a command list against a copy and return one publishable plan."""
    state = _copy_state(current)
    actions: list[PlannedAction] = []
    render_ids: set[str] = set()

    for command in commands:
        if isinstance(command, MoveCommand):
            state = _move(state, command)
            action: WorkspaceAction = "moved"
        elif isinstance(command, RemoveCommand):
            state = _remove(state, command)
            action = "removed"
            render_ids.discard(command.id)
        else:
            existed = command.id in state.commands
            state = _upsert(state, command)
            action = "updated" if existed else "created"
            render_ids.add(command.id)
        actions.append(PlannedAction(command.id, command.type, action))

    if commands:
        _validate_state(state, command=commands[-1])
    return BatchPlan(
        state=state,
        actions=tuple(actions),
        render_ids=frozenset(node_id for node_id in render_ids if node_id in state.commands),
        removed_ids=frozenset(
            node_id
            for node_id, old_command in current.commands.items()
            if node_id not in state.commands
            or state.commands[node_id].type != old_command.type
        ),
    )


def apply_layout_parents(
    layout_id: str,
    children: tuple[str, ...],
    *,
    known_ids: frozenset[str],
    parent_of: dict[str, str | None],
) -> dict[str, str | None]:
    """Compatibility helper for the original v0.2 layout validation contract."""
    for child in children:
        if child == layout_id:
            raise CompositionError(
                "cycle",
                f"layout {layout_id!r} cannot contain itself",
                command_id=layout_id,
                command_type="layout",
            )
        if child not in known_ids:
            raise CompositionError(
                "unknown_child",
                f"unknown child {child!r}",
                command_id=layout_id,
                command_type="layout",
            )
        current_parent = parent_of.get(child)
        if current_parent is not None and current_parent != layout_id:
            raise CompositionError(
                "already_composed",
                f"child {child!r} already in {current_parent!r}",
                command_id=layout_id,
                command_type="layout",
            )
        _reject_cycle(layout_id, child, parent_of)

    next_parents = dict(parent_of)
    for existing, parent in list(next_parents.items()):
        if parent == layout_id and existing not in children:
            next_parents[existing] = None
    for child in children:
        next_parents[child] = layout_id
    return next_parents


def _copy_state(state: WorkspaceState) -> WorkspaceState:
    return WorkspaceState(
        commands=dict(state.commands),
        parent_of=dict(state.parent_of),
        root_children=tuple(state.root_children),
    )


def _upsert(state: WorkspaceState, command: NodeCommand) -> WorkspaceState:
    existing = state.commands.get(command.id)
    if existing is not None and existing.type != command.type:
        raise CompositionError(
            "type_mismatch",
            f"id {command.id!r} is {existing.type}, got {command.type}",
            command_id=command.id,
            command_type=command.type,
        )

    commands = dict(state.commands)
    parents = dict(state.parent_of)
    root = list(state.root_children)

    if not isinstance(command, LayoutCommand):
        commands[command.id] = command
        if existing is None:
            parents[command.id] = None
            root.append(command.id)
        return WorkspaceState(commands, parents, tuple(root))

    next_parents = apply_layout_parents(
        command.id,
        command.children,
        known_ids=frozenset(state.commands),
        parent_of=state.parent_of,
    )
    old_children = existing.children if isinstance(existing, LayoutCommand) else ()
    dropped = [child for child in old_children if child not in command.children]

    if existing is None:
        parents[command.id] = None
        root.append(command.id)
    parents.update(next_parents)
    for child in command.children:
        if child in root:
            root.remove(child)
    for child in dropped:
        if child not in root:
            root.append(child)
    commands[command.id] = command
    return WorkspaceState(commands, parents, tuple(root))


def _move(state: WorkspaceState, command: MoveCommand) -> WorkspaceState:
    if command.id not in state.commands:
        raise _error("unknown_id", f"unknown id {command.id!r}", command)
    if command.parent is not None:
        parent_command = state.commands.get(command.parent)
        if parent_command is None:
            raise _error("invalid_parent", f"unknown parent {command.parent!r}", command)
        if not isinstance(parent_command, LayoutCommand):
            raise _error(
                "invalid_parent", f"parent {command.parent!r} is not a layout", command
            )
        _reject_move_cycle(state, command)

    old_parent = state.parent_of[command.id]
    source = list(_children(state, old_parent))
    source.remove(command.id)
    if old_parent == command.parent:
        destination = source
    else:
        destination = list(_children(state, command.parent))

    index = len(destination) if command.index is None else command.index
    if index > len(destination):
        raise _error(
            "invalid_index",
            f"index {index} is outside destination range 0..{len(destination)}",
            command,
        )
    if command.parent is not None and len(destination) + 1 > MAX_CHILDREN:
        raise _error(
            "limit_exceeded",
            f"layout {command.parent!r} exceeds limit of {MAX_CHILDREN} children",
            command,
        )
    destination.insert(index, command.id)

    next_state = _set_children(state, old_parent, tuple(source))
    next_state = _set_children(next_state, command.parent, tuple(destination))
    parents = dict(next_state.parent_of)
    parents[command.id] = command.parent
    return WorkspaceState(next_state.commands, parents, next_state.root_children)


def _remove(state: WorkspaceState, command: RemoveCommand) -> WorkspaceState:
    target = state.commands.get(command.id)
    if target is None:
        raise _error("unknown_id", f"unknown id {command.id!r}", command)

    parent = state.parent_of[command.id]
    siblings = list(_children(state, parent))
    siblings.remove(command.id)
    next_state = _set_children(state, parent, tuple(siblings))

    commands = dict(next_state.commands)
    parents = dict(next_state.parent_of)
    root = list(next_state.root_children)
    if isinstance(target, LayoutCommand):
        for child in target.children:
            parents[child] = None
            if child not in root:
                root.append(child)
    del commands[command.id]
    del parents[command.id]
    return WorkspaceState(commands, parents, tuple(root))


def _children(state: WorkspaceState, parent: str | None) -> tuple[str, ...]:
    return state.root_children if parent is None else _layout(state, parent).children


def _set_children(
    state: WorkspaceState, parent: str | None, children: tuple[str, ...]
) -> WorkspaceState:
    if parent is None:
        return WorkspaceState(dict(state.commands), dict(state.parent_of), children)
    commands = dict(state.commands)
    commands[parent] = replace(_layout(state, parent), children=children)
    return WorkspaceState(commands, dict(state.parent_of), state.root_children)


def _layout(state: WorkspaceState, layout_id: str) -> LayoutCommand:
    command = state.commands[layout_id]
    assert isinstance(command, LayoutCommand)
    return command


def _reject_move_cycle(state: WorkspaceState, command: MoveCommand) -> None:
    if command.parent is None or not isinstance(state.commands[command.id], LayoutCommand):
        return
    current: str | None = command.parent
    hops = 0
    while current is not None:
        if current == command.id:
            raise _error("cycle", f"move of {command.id!r} would create a cycle", command)
        hops += 1
        if hops > _SAFETY_HOPS:
            raise _error("limit_exceeded", "layout ancestry exceeds safety limit", command)
        current = state.parent_of[current]


def _reject_cycle(
    layout_id: str,
    child: str,
    parent_of: dict[str, str | None],
) -> None:
    current: str | None = layout_id
    hops = 0
    while current is not None:
        if current == child:
            raise CompositionError(
                "cycle",
                f"child {child!r} is an ancestor of {layout_id!r}",
                command_id=layout_id,
                command_type="layout",
            )
        hops += 1
        if hops > _SAFETY_HOPS:
            raise CompositionError(
                "limit_exceeded",
                "layout ancestry exceeds safety limit",
                command_id=layout_id,
                command_type="layout",
            )
        current = parent_of.get(current)


def _validate_state(state: WorkspaceState, *, command: Command) -> None:
    ids = set(state.commands)
    if set(state.parent_of) != ids:
        raise _error("invalid_state", "workspace parent map is inconsistent", command)

    memberships: list[str] = list(state.root_children)
    if len(set(state.root_children)) != len(state.root_children):
        raise _error("invalid_state", "duplicate root child", command)
    for layout_id, node in state.commands.items():
        if not isinstance(node, LayoutCommand):
            continue
        if len(node.children) > MAX_CHILDREN or len(set(node.children)) != len(node.children):
            raise _error("invalid_state", f"invalid children in layout {layout_id!r}", command)
        memberships.extend(node.children)
        for child in node.children:
            if child not in ids or state.parent_of[child] != layout_id:
                raise _error("invalid_state", f"invalid child {child!r}", command)

    if len(memberships) != len(ids) or set(memberships) != ids:
        raise _error("invalid_state", "nodes must occur in exactly one container", command)
    for root_id in state.root_children:
        if state.parent_of[root_id] is not None:
            raise _error("invalid_state", f"root child {root_id!r} has a parent", command)


def _error(code: str, message: str, command: Command) -> CompositionError:
    return CompositionError(
        code,
        message,
        command_id=command.id,
        command_type=command.type,
    )
