# Qt-free study intent, context, response policy, and session state.
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from surface.protocol import Command, NodeCommand, RemoveCommand, TextCommand

StudyMode = Literal[
    "hint_only",
    "next_step",
    "check_attempt",
    "show_solution",
    "new_variant",
]

MAX_STUDY_PROBLEM_LENGTH = 12_000
MAX_STUDY_ATTEMPT_LENGTH = 2_000

_SLOT_LIMITS: dict[str, int] = {
    "hint-1": 600,
    "attempt-1": MAX_STUDY_ATTEMPT_LENGTH,
    "feedback-1": 1_000,
    "step-1": 1_200,
}
_RESPONSE_SLOT: dict[StudyMode, str] = {
    "hint_only": "hint-1",
    "next_step": "step-1",
    "check_attempt": "feedback-1",
    "show_solution": "solution-1",
    "new_variant": "",
}
_STUDY_SLOTS = ("attempt-1", "hint-1", "feedback-1", "step-1", "solution-1")

_HINT = re.compile(r"\b(hint|hintet|ledetråd|ledetrad|clue)\b", re.IGNORECASE)
_HELP = re.compile(r"\b(hjelp|hjelpe|help)\b", re.IGNORECASE)
_NEXT = re.compile(
    r"\b(neste\s+steg|ett\s+neste\s+steg|next\s+step|one\s+next\s+step|fortsett|continue)\b",
    re.IGNORECASE,
)
_CHECK = re.compile(
    r"\b(er\s+det\s+riktig|stemmer|jeg\s+fikk|mitt\s+svar|svaret\s+mitt|"
    r"hvor\s+gjorde\s+jeg\s+feil|i\s+got|my\s+answer|is\s+(?:this|that|it)\s+right|"
    r"where\s+did\s+i\s+go\s+wrong|check\s+my)\b",
    re.IGNORECASE,
)
_SOLUTION = re.compile(
    r"\b(vis(?:e)?|gi|reveal|show)\b.{0,24}\b(hele\s+løsningen|full(?:e)?\s+løsning|fasit|"
    r"full\s+solution|whole\s+solution|complete\s+solution)\b|"
    r"\b(løs\s+hele\s+oppgaven|solve\s+the\s+whole\s+problem)\b",
    re.IGNORECASE,
)
_VARIANT = re.compile(
    r"\b(ny\s+variant|andre\s+tall|new\s+variant|different\s+(?:numbers|values))\b",
    re.IGNORECASE,
)
_VAGUE_SOLUTION = re.compile(
    r"\b(løs(?:ning|e)?|fasit|solve|solution|answer)\b", re.IGNORECASE
)
_NEGATED_SOLUTION = re.compile(
    r"\b(?:"
    r"ikke\s+(?:løs(?:e)?(?:\s+(?:oppgaven|problemet|den))?|"
    r"vis(?:e)?\s+(?:hele\s+)?(?:løsningen|fasit(?:en)?))|"
    r"uten\s+(?:(?:å\s+)?løs(?:e)?(?:\s+(?:oppgaven|problemet))?|(?:en\s+)?løsning)|"
    r"(?:do\s+not|don['’]t)\s+(?:solve(?:\s+(?:it|the\s+problem|the\s+task))?|"
    r"(?:show|reveal)\s+(?:the\s+)?(?:solution|answer))|"
    r"without\s+(?:solving(?:\s+(?:it|the\s+problem|the\s+task))?|"
    r"(?:(?:a|the)\s+)?solution)"
    r")\b",
    re.IGNORECASE,
)
_WORKSPACE_ACTION = re.compile(
    r"\b(flytt|fjern|slett|oppdater|move|remove|delete|update|reorder)\b",
    re.IGNORECASE,
)
_ATTEMPT_VALUE = re.compile(r"(?:\d|=|\b(?:mpa|kpa|pa|n|kn|mm|cm|m)\b)", re.IGNORECASE)
_CONTINUE_ONLY = re.compile(r"^\s*(fortsett|continue)[.!?]?\s*$", re.IGNORECASE)


class StudyWorkspace(Protocol):
    def get(self, command_id: str) -> NodeCommand | None: ...
    def list_ids(self) -> list[str]: ...


class StudyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class StudyState:
    target_id: str | None = None
    round: int = 0
    last_mode: StudyMode | None = None
    last_attempt_id: str | None = None
    solution_revealed: bool = False
    variant: int = 0


@dataclass(frozen=True)
class StudyTurn:
    mode: StudyMode
    target_id: str
    user_message: str
    prompt_context: dict[str, object]
    original_problem_content: str
    base_round: int
    base_variant: int
    attempt_text: str | None = None


class StudySession:
    def __init__(self) -> None:
        self._state = StudyState()

    @property
    def state(self) -> StudyState:
        return self._state

    def prepare(self, text: str, workspace: StudyWorkspace) -> StudyTurn | None:
        user_message = text.strip()
        mode = self._classify(user_message)
        if mode is None:
            return None
        if _CONTINUE_ONLY.fullmatch(user_message) and self._state.target_id is None:
            raise StudyError("study_not_active", "no active study interaction to continue")

        target_id, problem = self._resolve_problem(workspace)
        self._validate_slots(workspace)
        if len(problem.content) > MAX_STUDY_PROBLEM_LENGTH:
            raise StudyError(
                "study_content_too_large",
                f"problem content exceeds {MAX_STUDY_PROBLEM_LENGTH} characters",
            )

        attempt_text: str | None = None
        prior: dict[str, str] = {}
        if mode == "check_attempt":
            if self._has_new_attempt(user_message):
                if len(user_message) > MAX_STUDY_ATTEMPT_LENGTH:
                    raise StudyError(
                        "study_attempt_too_large",
                        f"attempt exceeds {MAX_STUDY_ATTEMPT_LENGTH} characters",
                    )
                attempt_text = user_message
                prior["attempt"] = user_message
            else:
                previous_attempt = self._slot_content(workspace, "attempt-1")
                if previous_attempt is None:
                    raise StudyError(
                        "study_attempt_missing",
                        "submit an attempt before asking where it went wrong",
                    )
                prior["attempt"] = previous_attempt
        else:
            for label, slot_id in self._prior_slots(mode):
                content = self._slot_content(workspace, slot_id)
                if content is not None:
                    prior[label] = content

        response_id = target_id if mode == "new_variant" else _RESPONSE_SLOT[mode]
        response: dict[str, object] = {"type": "text", "id": response_id}
        limit = self._response_limit(mode)
        if limit is not None:
            response["max_chars"] = limit
        context: dict[str, object] = {
            "study": {
                "mode": mode,
                "target_id": target_id,
                "round": self._state.round,
                "solution_revealed": self._state.solution_revealed,
                "user_message": user_message,
                "problem": {
                    "id": target_id,
                    "type": "text",
                    "content": problem.content,
                },
                "prior": prior,
                "response": response,
            }
        }
        return StudyTurn(
            mode=mode,
            target_id=target_id,
            user_message=user_message,
            prompt_context=context,
            original_problem_content=problem.content,
            base_round=self._state.round,
            base_variant=self._state.variant,
            attempt_text=attempt_text,
        )

    def finalize(
        self,
        turn: StudyTurn,
        hermes_commands: list[Command],
        workspace: StudyWorkspace,
    ) -> list[Command]:
        if turn.base_round != self._state.round or turn.base_variant != self._state.variant:
            raise StudyError("study_turn_stale", "study state changed while Hermes was running")
        if len(hermes_commands) != 1 or not isinstance(hermes_commands[0], TextCommand):
            raise StudyError(
                "invalid_study_response",
                "study response must contain exactly one text command",
            )
        response = hermes_commands[0]
        expected_id = turn.target_id if turn.mode == "new_variant" else _RESPONSE_SLOT[turn.mode]
        if response.id != expected_id:
            raise StudyError(
                "invalid_study_response",
                f"study response must update {expected_id!r}",
            )
        limit = self._response_limit(turn.mode)
        if limit is not None and len(response.content) > limit:
            raise StudyError(
                "study_response_too_large",
                f"study response exceeds {limit} characters",
            )
        if turn.mode == "new_variant" and response.content == turn.original_problem_content:
            raise StudyError(
                "invalid_study_response", "new variant must change the problem content"
            )

        commands: list[Command] = []
        if turn.mode == "check_attempt" and turn.attempt_text is not None:
            commands.append(
                TextCommand(
                    type="text", id="attempt-1", content=turn.attempt_text, format="plain"
                )
            )
        commands.append(response)
        if turn.mode == "new_variant":
            commands.extend(
                RemoveCommand(type="remove", id=slot_id)
                for slot_id in _STUDY_SLOTS
                if workspace.get(slot_id) is not None
            )
        return commands

    def commit(self, turn: StudyTurn) -> None:
        if turn.base_round != self._state.round or turn.base_variant != self._state.variant:
            raise StudyError("study_turn_stale", "study state changed before commit")
        if turn.mode == "new_variant":
            self._state = StudyState(
                target_id=turn.target_id,
                round=0,
                last_mode="new_variant",
                last_attempt_id=None,
                solution_revealed=False,
                variant=self._state.variant + 1,
            )
            return
        self._state = StudyState(
            target_id=turn.target_id,
            round=self._state.round + 1,
            last_mode=turn.mode,
            last_attempt_id=(
                "attempt-1"
                if turn.mode == "check_attempt" and turn.attempt_text is not None
                else self._state.last_attempt_id
            ),
            solution_revealed=(
                self._state.solution_revealed or turn.mode == "show_solution"
            ),
            variant=self._state.variant,
        )

    def _classify(self, text: str) -> StudyMode | None:
        solution_text = _NEGATED_SOLUTION.sub(" ", text)
        explicit: set[StudyMode] = set()
        if _HINT.search(text):
            explicit.add("hint_only")
        if _NEXT.search(text):
            explicit.add("next_step")
        if _CHECK.search(text):
            explicit.add("check_attempt")
        if _SOLUTION.search(solution_text):
            explicit.add("show_solution")
        if _VARIANT.search(text):
            explicit.add("new_variant")
        if len(explicit) > 1:
            raise StudyError(
                "ambiguous_study_request",
                "ask for one of: hint, feedback, next step, new variant, or full solution",
            )
        if explicit:
            return next(iter(explicit))
        if _WORKSPACE_ACTION.search(text):
            return None
        if _HELP.search(text):
            return "hint_only"
        if self._state.target_id is not None and _ATTEMPT_VALUE.search(text):
            return "check_attempt"
        if _VAGUE_SOLUTION.search(solution_text):
            raise StudyError(
                "ambiguous_study_request",
                "say explicitly whether you want a hint, one next step, or the full solution",
            )
        return None

    def _resolve_problem(self, workspace: StudyWorkspace) -> tuple[str, TextCommand]:
        if self._state.target_id is not None:
            current = workspace.get(self._state.target_id)
            if current is None:
                raise StudyError("study_target_missing", "the active problem no longer exists")
            if not isinstance(current, TextCommand):
                raise StudyError("study_target_invalid", "the active problem is not text")
            return self._state.target_id, current

        exact = workspace.get("problem-1")
        if exact is not None:
            if not isinstance(exact, TextCommand):
                raise StudyError("study_target_invalid", "problem-1 is not a text block")
            return "problem-1", exact
        candidates = [
            node_id
            for node_id in workspace.list_ids()
            if node_id.startswith("problem-")
            and isinstance(workspace.get(node_id), TextCommand)
        ]
        if not candidates:
            raise StudyError("study_target_missing", "no text problem is available")
        if len(candidates) > 1:
            raise StudyError("study_target_ambiguous", "multiple problem blocks are available")
        command = workspace.get(candidates[0])
        assert isinstance(command, TextCommand)
        return candidates[0], command

    def _validate_slots(self, workspace: StudyWorkspace) -> None:
        for slot_id in _STUDY_SLOTS:
            command = workspace.get(slot_id)
            if command is not None and not isinstance(command, TextCommand):
                raise StudyError(
                    "study_slot_conflict", f"reserved study id {slot_id!r} is not text"
                )
            if isinstance(command, TextCommand):
                limit = _SLOT_LIMITS.get(slot_id)
                if limit is not None and len(command.content) > limit:
                    raise StudyError(
                        "study_context_too_large",
                        f"study slot {slot_id!r} exceeds {limit} characters",
                    )

    @staticmethod
    def _prior_slots(mode: StudyMode) -> tuple[tuple[str, str], ...]:
        if mode == "hint_only":
            return (("hint", "hint-1"),)
        if mode == "next_step":
            return (
                ("hint", "hint-1"),
                ("feedback", "feedback-1"),
                ("step", "step-1"),
            )
        if mode == "show_solution":
            return (
                ("attempt", "attempt-1"),
                ("feedback", "feedback-1"),
                ("step", "step-1"),
            )
        return ()

    @staticmethod
    def _slot_content(workspace: StudyWorkspace, slot_id: str) -> str | None:
        command = workspace.get(slot_id)
        return command.content if isinstance(command, TextCommand) else None

    @staticmethod
    def _has_new_attempt(text: str) -> bool:
        return _ATTEMPT_VALUE.search(text) is not None or bool(
            re.search(r"\b(jeg\s+fikk|mitt\s+svar|svaret\s+mitt|i\s+got|my\s+answer)\b", text, re.I)
        )

    @staticmethod
    def _response_limit(mode: StudyMode) -> int | None:
        if mode == "new_variant":
            return MAX_STUDY_PROBLEM_LENGTH
        slot_id = _RESPONSE_SLOT[mode]
        return _SLOT_LIMITS.get(slot_id)
