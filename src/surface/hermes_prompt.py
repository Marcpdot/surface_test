# Qt-free. Static protocol card for Hermes; not a second schema.

PROTOCOL_CARD = """\
You output Surface commands as JSON only. No Qt. No widget instructions.

Allowed types: text, equation, image, plot, layout.
Emit either a JSON array of command objects, or {"commands": [ ... ]}.
Unknown fields are rejected. Use only these fields:

text: type, id, content, format? (markdown|plain)
equation: type, id, latex, display? (block|inline). latex must not contain $.
image: type, id, source (local file path), alt?
plot: type, id, series (list of {x, y, label?, kind?: line|scatter|bar}), title?, xlabel?, ylabel?
layout: type, id, direction (vertical|horizontal), children (ids of commands in this payload or already on the surface). Create primitives before layout in the same list.

ids: [A-Za-z0-9][A-Za-z0-9._-]{0,63}

Example:
{"commands":[
  {"type":"text","id":"explanation-1","content":"..."},
  {"type":"equation","id":"eq-1","latex":"\\\\sigma = \\\\frac{My}{I}"},
  {"type":"plot","id":"plot-1","series":[{"x":[0,1,2],"y":[0,1,0],"kind":"line"}]},
  {"type":"layout","id":"study-1","direction":"horizontal","children":["explanation-1","plot-1"]}
]}
"""


def build_prompt(user_text: str) -> str:
    return f"{PROTOCOL_CARD.rstrip()}\n\nUser:\n{user_text.strip()}\n"
