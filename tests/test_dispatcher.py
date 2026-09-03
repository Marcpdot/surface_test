from typing import Literal

from surface.dispatcher import (
    Dispatcher,
    DispatchResult,
    TypeMismatchError,
    UnknownBlockError,
)
from surface.protocol import (
    Command,
    EquationCommand,
    ImageCommand,
    PlotCommand,
    Series,
    TextCommand,
)


class FakeWorkspace:
    def __init__(self) -> None:
        self.commands: dict[str, Command] = {}

    def upsert(self, command: Command) -> Literal["created", "updated"]:
        existing = self.commands.get(command.id)
        if existing is None:
            self.commands[command.id] = command
            return "created"
        if existing.type != command.type:
            raise TypeMismatchError(command.id, existing.type, command.type)
        self.commands[command.id] = command
        return "updated"

    def get(self, command_id: str) -> Command | None:
        return self.commands.get(command_id)

    def remove(self, command_id: str) -> bool:
        return self.commands.pop(command_id, None) is not None

    def list_ids(self) -> list[str]:
        return list(self.commands)


class _UnknownBlockWorkspace(FakeWorkspace):
    def upsert(self, command: Command) -> Literal["created", "updated"]:
        raise UnknownBlockError(command.id, command.type)


def test_text_created_then_updated() -> None:
    workspace = FakeWorkspace()
    dispatcher = Dispatcher(workspace)
    first = TextCommand(type="text", id="t-1", content="hello")
    created = dispatcher.dispatch(first)
    assert created == DispatchResult(
        ok=True,
        action="created",
        command_id="t-1",
        command_type="text",
        error_code=None,
        error_message=None,
    )
    assert workspace.get("t-1") == first

    second = TextCommand(type="text", id="t-1", content="world")
    updated = dispatcher.dispatch(second)
    assert updated.ok is True
    assert updated.action == "updated"
    assert updated.command_id == "t-1"
    assert updated.command_type == "text"
    assert workspace.get("t-1") == second


def test_equation_image_plot_are_stored() -> None:
    workspace = FakeWorkspace()
    dispatcher = Dispatcher(workspace)
    equation = EquationCommand(type="equation", id="eq-1", latex=r"\sigma = \frac{My}{I}")
    image = ImageCommand(type="image", id="img-1", source=r"C:\course\beam.png")
    plot = PlotCommand(
        type="plot",
        id="plot-1",
        series=(Series(x=(0.0, 1.0), y=(0.0, 1.0)),),
    )
    assert dispatcher.dispatch(equation).action == "created"
    assert dispatcher.dispatch(image).action == "created"
    assert dispatcher.dispatch(plot).action == "created"
    assert workspace.get("eq-1") == equation
    assert workspace.get("img-1") == image
    assert workspace.get("plot-1") == plot


def test_type_mismatch_reports_new_type() -> None:
    workspace = FakeWorkspace()
    dispatcher = Dispatcher(workspace)
    original = TextCommand(type="text", id="x", content="hello")
    dispatcher.dispatch(original)
    result = dispatcher.dispatch(EquationCommand(type="equation", id="x", latex="a"))
    assert result.ok is False
    assert result.action is None
    assert result.error_code == "type_mismatch"
    assert result.command_id == "x"
    assert result.command_type == "equation"
    assert workspace.get("x") == original


def test_unknown_block() -> None:
    workspace = _UnknownBlockWorkspace()
    dispatcher = Dispatcher(workspace)
    command = TextCommand(type="text", id="t-1", content="hello")
    result = dispatcher.dispatch(command)
    assert result.ok is False
    assert result.action is None
    assert result.error_code == "unknown_block"
    assert result.command_id == "t-1"
    assert result.command_type == "text"
    assert result.error_message == "no block registered for type 'text'"
    assert workspace.list_ids() == []


def test_dispatch_many_mismatch_leaves_prior_command() -> None:
    workspace = FakeWorkspace()
    dispatcher = Dispatcher(workspace)
    valid = TextCommand(type="text", id="a", content="one")
    mismatch = EquationCommand(type="equation", id="a", latex="x")
    results = dispatcher.dispatch_many([valid, mismatch])
    assert results[0].ok is True
    assert results[0].action == "created"
    assert results[1].ok is False
    assert results[1].error_code == "type_mismatch"
    assert results[1].command_type == "equation"
    assert workspace.list_ids() == ["a"]
    assert workspace.get("a") == valid


def test_dispatch_many_continues_after_mismatch() -> None:
    workspace = FakeWorkspace()
    dispatcher = Dispatcher(workspace)
    first = TextCommand(type="text", id="a", content="one")
    mismatch = EquationCommand(type="equation", id="a", latex="x")
    third = TextCommand(type="text", id="b", content="two")
    results = dispatcher.dispatch_many([first, mismatch, third])
    assert [result.ok for result in results] == [True, False, True]
    assert results[2].action == "created"
    assert workspace.get("a") == first
    assert workspace.get("b") == third
