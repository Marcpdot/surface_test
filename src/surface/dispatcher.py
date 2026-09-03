# Qt-free by design.
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol as TypingProtocol

from surface.protocol import Command


class TypeMismatchError(Exception):
    def __init__(self, command_id: str, existing_type: str, new_type: str) -> None:
        self.command_id = command_id
        self.existing_type = existing_type
        self.new_type = new_type
        super().__init__(
            f"id {command_id!r} is {existing_type}, got {new_type}"
        )


class UnknownBlockError(Exception):
    def __init__(self, command_id: str, command_type: str) -> None:
        self.command_id = command_id
        self.command_type = command_type
        super().__init__(f"no block registered for type {command_type!r}")


class WorkspaceLike(TypingProtocol):
    def upsert(self, command: Command) -> Literal["created", "updated"]: ...
    def get(self, command_id: str) -> Command | None: ...
    def remove(self, command_id: str) -> bool: ...
    def list_ids(self) -> list[str]: ...


@dataclass(frozen=True)
class DispatchResult:
    ok: bool
    action: Literal["created", "updated"] | None
    command_id: str | None
    command_type: str | None  # innkommende type; ved type_mismatch er dette new_type
    error_code: str | None
    error_message: str | None


class Dispatcher:
    def __init__(self, workspace: WorkspaceLike) -> None:
        self._workspace = workspace

    def dispatch(self, command: Command) -> DispatchResult:
        """Upsert én allerede parset Command.

        Never raises ProtocolError, TypeMismatchError or UnknownBlockError.
        Render-feil skal ikke nå hit (`Block.render` kaster aldri).
        Unexpected exceptions propagate (programmeringsfeil).
        """
        try:
            action = self._workspace.upsert(command)
            return DispatchResult(
                ok=True,
                action=action,
                command_id=command.id,
                command_type=command.type,
                error_code=None,
                error_message=None,
            )
        except TypeMismatchError as exc:
            return DispatchResult(
                False, None, exc.command_id, exc.new_type, "type_mismatch", str(exc)
            )
        except UnknownBlockError as exc:
            return DispatchResult(
                False, None, exc.command_id, exc.command_type, "unknown_block", str(exc)
            )

    def dispatch_many(self, commands: list[Command]) -> list[DispatchResult]:
        """Sekvensiell dispatch. Returnerer én DispatchResult per element.

        Parse er kallerens jobb (bro / tester kaller parse_command_list først).
        """
        return [self.dispatch(command) for command in commands]
