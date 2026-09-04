# Qt-free. Static protocol card for Hermes; not a second schema.
import json
from collections.abc import Mapping

PROTOCOL_CARD = """\
You output Surface commands as JSON only. No Qt. No widget instructions.

Reply with one JSON value and nothing else.
Do not write markdown. Do not wrap the JSON in ``` or ```json fences.
Do not write any explanation before or after the JSON.
The first non-whitespace character must be { or [.
The last non-whitespace character must be } or ].

Allowed types: text, equation, image, plot, layout, move, remove.
Emit either a JSON array of command objects, or {"commands": [ ... ]}.
Unknown fields are rejected. Use only these fields:

text: type, id, content, format? (markdown|plain)
equation: type, id, latex, display? (block|inline). latex must not contain $.
image: type, id, source (local file path), alt?
plot: type, id, series (list of {x, y, label?, kind?: line|scatter|bar}), title?, xlabel?, ylabel?
layout: type, id, direction (vertical|horizontal), children (ids of commands in this payload or already on the surface). Create primitives before layout in the same list.
move: type, id (an existing node), parent (an existing layout id or null for root), index? (zero-based; omitted appends). Moving within the same parent reorders.
remove: type, id (an existing node). Removing a layout preserves its direct children at root.

For updates, move, and remove, use ids from Current workspace. Do not invent an id for an existing node.
Primitive upserts update content without changing placement.

ids: [A-Za-z0-9][A-Za-z0-9._-]{0,63}

Example:
{"commands":[
  {"type":"text","id":"explanation-1","content":"..."},
  {"type":"equation","id":"eq-1","latex":"\\\\sigma = \\\\frac{My}{I}"},
  {"type":"plot","id":"plot-1","series":[{"x":[0,1,2],"y":[0,1,0],"kind":"line"}]},
  {"type":"layout","id":"study-1","direction":"horizontal","children":["explanation-1","plot-1"]}
]}
"""


def build_prompt(
    user_text: str,
    workspace_snapshot: Mapping[str, object] | None = None,
    study_context: Mapping[str, object] | None = None,
) -> str:
    snapshot = {"nodes": []} if workspace_snapshot is None else workspace_snapshot
    serialized = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    study_section = ""
    if study_context is not None:
        study = study_context.get("study")
        mode = study.get("mode") if isinstance(study, Mapping) else None
        serialized_study = json.dumps(
            study_context, ensure_ascii=False, separators=(",", ":")
        )
        study_section = (
            "Study turn (Surface-controlled; obey exactly):\n"
            f"{serialized_study}\n"
            f"Study policy: {_study_policy(mode)}\n"
            "Return exactly the one text command described by study.response. "
            "Do not add, move, remove, or update any other id.\n\n"
        )
    return (
        f"{PROTOCOL_CARD.rstrip()}\n\n"
        f"Current workspace (Surface semantic state; no Qt):\n{serialized}\n\n"
        f"{study_section}"
        f"User:\n{user_text.strip()}\n\n"
        "JSON only. No markdown fences. First character { or [.\n"
    )


def _study_policy(mode: object) -> str:
    if mode == "hint_only":
        return "Give one short direction or reminder only. No derivation and no final answer."
    if mode == "check_attempt":
        return (
            "Assess the supplied attempt briefly. State what is right or wrong and give at "
            "most one corrective hint. Do not continue the solution."
        )
    if mode == "next_step":
        return "Give exactly one next derivation or action. Do not give later steps or the final answer."
    if mode == "show_solution":
        return "The user explicitly requested it; give the complete solution with reasoning."
    if mode == "new_variant":
        return (
            "Change the numerical values while preserving the same problem type, method, and "
            "difficulty. Return only the revised problem text."
        )
    return "The study mode is invalid; do not generate a response."
