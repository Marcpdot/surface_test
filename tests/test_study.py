from __future__ import annotations

import pytest

from surface.composition import PlannedAction, WorkspaceState, plan_batch
from surface.dispatcher import Dispatcher
from surface.hermes_bridge import HermesBridge
from surface.hermes_transport import FakeTransport
from surface.protocol import (
    Command,
    EquationCommand,
    LayoutCommand,
    ProtocolError,
    RemoveCommand,
    TextCommand,
)
from surface.study import (
    MAX_STUDY_ATTEMPT_LENGTH,
    MAX_STUDY_PROBLEM_LENGTH,
    StudyError,
    StudySession,
)


class FakeWorkspace:
    def __init__(self) -> None:
        self.state = WorkspaceState.empty()

    def apply_many(self, commands: list[Command]) -> list[PlannedAction]:
        plan = plan_batch(self.state, commands)
        self.state = plan.state
        return list(plan.actions)

    def get(self, command_id: str):
        return self.state.commands.get(command_id)

    def list_ids(self) -> list[str]:
        return list(self.state.commands)

    def snapshot(self) -> dict[str, object]:
        return self.state.snapshot()


def _workspace(*commands: Command) -> FakeWorkspace:
    workspace = FakeWorkspace()
    results = Dispatcher(workspace).dispatch_many(list(commands))
    assert all(result.ok for result in results)
    return workspace


def _problem() -> TextCommand:
    return TextCommand(
        type="text",
        id="problem-1",
        content="A beam has b=50 mm, h=100 mm and M=5 kN m. Find maximum stress.",
    )


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("Gi meg bare et hint", "hint_only"),
        ("Give me one hint", "hint_only"),
        ("Vis ett neste steg, men ikke løs resten", "next_step"),
        ("Show one next step", "next_step"),
        ("Jeg fikk 60 MPa. Er det riktig?", "check_attempt"),
        ("My answer is 60 MPa. Is that right?", "check_attempt"),
        ("Nå kan du vise hele løsningen", "show_solution"),
        ("Show the full solution", "show_solution"),
        ("Lag en ny variant med andre tall", "new_variant"),
        ("Create a new variant with different numbers", "new_variant"),
    ],
)
def test_routes_explicit_study_modes(text: str, mode: str) -> None:
    turn = StudySession().prepare(text, _workspace(_problem()))
    assert turn is not None
    assert turn.mode == mode


def test_generic_help_is_safe_hint_and_workspace_request_is_not_study() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    assert session.prepare("Kan du hjelpe meg?", workspace).mode == "hint_only"  # type: ignore[union-attr]
    assert session.prepare("Flytt problemblokken til root", workspace) is None
    assert session.prepare("Fjern solution-1", workspace) is None
    assert session.prepare("Help me move the plot", workspace) is None


def test_ambiguous_and_vague_solution_requests_are_rejected() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    for text in ("Vis et hint og hele løsningen", "Kan du løse oppgaven?"):
        with pytest.raises(StudyError) as exc_info:
            session.prepare(text, workspace)
        assert exc_info.value.code == "ambiguous_study_request"


@pytest.mark.parametrize(
    "text",
    [
        "Ikke løs oppgaven",
        "Lag en mekanikkoppgave uten løsning",
        "Ikke vis fasit",
        "Create a mechanics problem, but don't solve it",
        "Do not solve it",
        "Create an exercise, but do not show the solution",
    ],
)
def test_negated_solution_language_is_not_study_intent(text: str) -> None:
    assert StudySession().prepare(text, _workspace()) is None


@pytest.mark.parametrize(
    "text",
    ["Vis løsning", "Show solution", "Kan du løse den?"],
)
def test_positive_vague_solution_language_stays_guarded(text: str) -> None:
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare(text, _workspace())
    assert exc_info.value.code == "ambiguous_study_request"


def test_continue_requires_active_session_then_routes_to_next_step() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    with pytest.raises(StudyError) as exc_info:
        session.prepare("Fortsett", workspace)
    assert exc_info.value.code == "study_not_active"
    hint = session.prepare("Bare et hint", workspace)
    assert hint is not None
    session.commit(hint)
    assert session.prepare("Fortsett", workspace).mode == "next_step"  # type: ignore[union-attr]


def test_attempt_value_routes_only_during_active_session() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    assert session.prepare("60 MPa", workspace) is None
    hint = session.prepare("hint", workspace)
    assert hint is not None
    session.commit(hint)
    attempt = session.prepare("60 MPa", workspace)
    assert attempt is not None
    assert attempt.mode == "check_attempt"
    assert attempt.attempt_text == "60 MPa"


def test_where_wrong_requires_previous_attempt() -> None:
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("Hvor gjorde jeg feil?", _workspace(_problem()))
    assert exc_info.value.code == "study_attempt_missing"


def test_target_resolution_and_slot_validation() -> None:
    unique = _workspace(TextCommand(type="text", id="problem-beam", content="p"))
    assert StudySession().prepare("hint", unique).target_id == "problem-beam"  # type: ignore[union-attr]

    missing = _workspace(TextCommand(type="text", id="notes", content="n"))
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("hint", missing)
    assert exc_info.value.code == "study_target_missing"

    ambiguous = _workspace(
        TextCommand(type="text", id="problem-a", content="a"),
        TextCommand(type="text", id="problem-b", content="b"),
    )
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("hint", ambiguous)
    assert exc_info.value.code == "study_target_ambiguous"

    invalid = _workspace(EquationCommand(type="equation", id="problem-1", latex="x"))
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("hint", invalid)
    assert exc_info.value.code == "study_target_invalid"

    collision = _workspace(
        _problem(), EquationCommand(type="equation", id="hint-1", latex="x")
    )
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("hint", collision)
    assert exc_info.value.code == "study_slot_conflict"


def test_study_input_limits() -> None:
    too_large = _workspace(
        TextCommand(
            type="text", id="problem-1", content="p" * (MAX_STUDY_PROBLEM_LENGTH + 1)
        )
    )
    with pytest.raises(StudyError) as exc_info:
        StudySession().prepare("hint", too_large)
    assert exc_info.value.code == "study_content_too_large"

    session = StudySession()
    workspace = _workspace(_problem())
    text = "Jeg fikk " + "1" * MAX_STUDY_ATTEMPT_LENGTH
    with pytest.raises(StudyError) as exc_info:
        session.prepare(text, workspace)
    assert exc_info.value.code == "study_attempt_too_large"


def test_context_contains_only_relevant_content() -> None:
    workspace = _workspace(
        _problem(),
        TextCommand(type="text", id="notes", content="private notes"),
        TextCommand(type="text", id="hint-1", content="old hint"),
        TextCommand(type="text", id="feedback-1", content="old feedback"),
    )
    turn = StudySession().prepare("Vis neste steg", workspace)
    assert turn is not None
    serialized = str(turn.prompt_context)
    assert "old hint" in serialized
    assert "old feedback" in serialized
    assert "private notes" not in serialized
    assert "Find maximum stress" in serialized


def test_response_contract_and_state_commit() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    turn = session.prepare("bare et hint", workspace)
    assert turn is not None
    before = session.state

    with pytest.raises(StudyError):
        session.finalize(
            turn,
            [
                TextCommand(type="text", id="hint-1", content="h"),
                TextCommand(type="text", id="solution-1", content="solution"),
            ],
            workspace,
        )
    assert session.state == before
    with pytest.raises(StudyError):
        session.finalize(
            turn, [TextCommand(type="text", id="solution-1", content="solution")], workspace
        )
    with pytest.raises(StudyError) as exc_info:
        session.finalize(
            turn, [TextCommand(type="text", id="hint-1", content="h" * 601)], workspace
        )
    assert exc_info.value.code == "study_response_too_large"

    commands = session.finalize(
        turn, [TextCommand(type="text", id="hint-1", content="Use I=bh^3/12.")], workspace
    )
    assert Dispatcher(workspace).dispatch_many(commands)[0].ok
    session.commit(turn)
    assert session.state.round == 1
    assert session.state.last_mode == "hint_only"
    assert session.state.solution_revealed is False


def test_transport_failure_does_not_advance_or_mutate_study() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    turn = session.prepare("bare et hint", workspace)
    assert turn is not None
    state_before = session.state
    workspace_before = workspace.snapshot()
    with pytest.raises(ProtocolError):
        HermesBridge().complete(
            turn.user_message,
            FakeTransport(error=ProtocolError("hermes_failed", "boom")),
            workspace.snapshot(),
            turn.prompt_context,
        )
    assert session.state == state_before
    assert workspace.snapshot() == workspace_before


def test_attempt_and_feedback_are_one_atomic_batch() -> None:
    session = StudySession()
    workspace = _workspace(_problem())
    turn = session.prepare("Jeg fikk 60 MPa. Er det riktig?", workspace)
    assert turn is not None
    commands = session.finalize(
        turn,
        [TextCommand(type="text", id="feedback-1", content="Ja, det er riktig.")],
        workspace,
    )
    assert [command.id for command in commands] == ["attempt-1", "feedback-1"]
    results = Dispatcher(workspace).dispatch_many(commands)
    assert all(result.ok for result in results)
    session.commit(turn)
    assert session.state.last_attempt_id == "attempt-1"


def test_new_variant_updates_target_and_removes_only_study_slots() -> None:
    session = StudySession()
    workspace = _workspace(
        _problem(),
        TextCommand(type="text", id="hint-1", content="hint"),
        TextCommand(type="text", id="notes", content="keep"),
    )
    turn = session.prepare("Lag en ny variant med andre tall", workspace)
    assert turn is not None
    with pytest.raises(StudyError):
        session.finalize(turn, [_problem()], workspace)
    revised = TextCommand(
        type="text", id="problem-1", content="Same beam method, now b=40 mm and h=80 mm."
    )
    commands = session.finalize(turn, [revised], workspace)
    assert commands == [revised, RemoveCommand(type="remove", id="hint-1")]
    results = Dispatcher(workspace).dispatch_many(commands)
    assert all(result.ok for result in results)
    session.commit(turn)
    assert workspace.get("problem-1") == revised
    assert workspace.get("hint-1") is None
    assert workspace.get("notes") is not None
    assert session.state.variant == 1
    assert session.state.round == 0
    assert session.state.solution_revealed is False


def test_fake_hermes_multi_round_study_loop() -> None:
    workspace = _workspace(
        _problem(),
        TextCommand(type="text", id="figure-note", content="keep me"),
        LayoutCommand(
            type="layout",
            id="study-1",
            direction="vertical",
            children=("problem-1", "figure-note"),
        ),
    )
    dispatcher = Dispatcher(workspace)
    bridge = HermesBridge()
    session = StudySession()

    rounds = [
        ("Gi meg bare et hint", '{"type":"text","id":"hint-1","content":"Start with I=bh^3/12."}'),
        (
            "Jeg fikk 60 MPa. Er det riktig?",
            '{"type":"text","id":"feedback-1","content":"Yes. Your unit conversion and result are correct."}',
        ),
        (
            "Vis ett neste steg, men ikke løs resten",
            '{"type":"text","id":"step-1","content":"Substitute b and h into I=bh^3/12."}',
        ),
    ]
    for user_text, output in rounds:
        turn = session.prepare(user_text, workspace)
        assert turn is not None
        transport = FakeTransport(output=output)
        model_commands = bridge.complete(
            user_text, transport, workspace.snapshot(), turn.prompt_context
        )
        commands = session.finalize(turn, model_commands, workspace)
        results = dispatcher.dispatch_many(commands)
        assert all(result.ok for result in results)
        session.commit(turn)
        assert '"study"' in transport.prompts[0]

    assert session.state.round == 3
    assert workspace.get("solution-1") is None
    assert workspace.state.parent_of["problem-1"] == "study-1"

    solution_text = "Nå kan du vise hele løsningen"
    solution_turn = session.prepare(solution_text, workspace)
    assert solution_turn is not None
    solution_commands = bridge.complete(
        solution_text,
        FakeTransport(
            output='{"type":"text","id":"solution-1","content":"Compute I, use y=h/2, then sigma=My/I=60 MPa."}'
        ),
        workspace.snapshot(),
        solution_turn.prompt_context,
    )
    finalized = session.finalize(solution_turn, solution_commands, workspace)
    assert all(result.ok for result in dispatcher.dispatch_many(finalized))
    session.commit(solution_turn)
    assert session.state.solution_revealed is True
    assert workspace.get("solution-1") is not None


def test_ordinary_generated_exercise_becomes_stable_study_target() -> None:
    request = "Create a mechanics problem for me, but do not solve the problem."
    assert StudySession().prepare(request, _workspace()) is None
    transport = FakeTransport(
        output=(
            '{"type":"text","id":"problem-1",'
            '"content":"A 10 kg mass rests on a 30 degree incline. Find the force."}'
        )
    )
    commands = HermesBridge().complete(request, transport, {"nodes": []})
    assert "use id problem-1 for the primary text block" in transport.prompts[0]

    workspace = _workspace(*commands)
    turn = StudySession().prepare("Gi meg bare ett hint til denne oppgaven", workspace)
    assert turn is not None
    assert turn.target_id == "problem-1"
