# Qt-free by design.
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol as TypingProtocol

from surface.composition import CompositionError, PlannedAction, WorkspaceAction
from surface.protocol import Command, NodeCommand


class TypeMismatchError(Exception):
    def __init__(self, command_id: str, existing_type: str, new_type: str) -> None:
        self.command_id = command_id
        self.existing_type = existing_type
        self.new_type = new_type
        super().__init__(f"id {command_id!r} is {existing_type}, got {new_type}")


class UnknownBlockError(Exception):
    def __init__(self, command_id: str, command_type: str) -> None:
        self.command_id = command_id
        self.command_type = command_type
        super().__init__(f"no block registered for type {command_type!r}")


class WorkspaceLike(TypingProtocol):
    def apply_many(self, commands: list[Command]) -> list[PlannedAction]: ...
    def get(self, command_id: str) -> NodeCommand | None: ...
    def list_ids(self) -> list[str]: ...


@dataclass(frozen=True)
class DispatchResult:
    ok: bool
    action: WorkspaceAction | None
    command_id: str | None
    command_type: str | None
    error_code: str | None
    error_message: str | None


class Dispatcher:
    def __init__(self, workspace: WorkspaceLike) -> None:
        self._workspace = workspace

    def dispatch(self, command: Command) -> DispatchResult:
        return self.dispatch_many([command])[0]

    def dispatch_many(self, commands: list[Command]) -> list[DispatchResult]:
        """Apply one command list atomically; a rejected batch mutates nothing."""
        if not commands:
            return []
        try:
            actions = self._workspace.apply_many(commands)
        except TypeMismatchError as exc:
            return [
                DispatchResult(
                    False, None, exc.command_id, exc.new_type, "type_mismatch", str(exc)
                )
            ]
        except UnknownBlockError as exc:
            return [
                DispatchResult(
                    False, None, exc.command_id, exc.command_type, "unknown_block", str(exc)
                )
            ]
        except CompositionError as exc:
            return [
                DispatchResult(
                    False,
                    None,
                    exc.command_id,
                    exc.command_type,
                    exc.code,
                    str(exc),
                )
            ]
        return [
            DispatchResult(
                ok=True,
                action=item.action,
                command_id=item.command_id,
                command_type=item.command_type,
                error_code=None,
                error_message=None,
            )
            for item in actions
        ]
