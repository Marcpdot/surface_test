# hermes_prompt.py

Source: `src/surface/hermes_prompt.py`

**Hva er ansvaret?**  
Statisk protocol-kort som forteller Hermes hvilke command-typer og felt som er gyldige.

**Hvordan går data inn og ut?**  
For vanlig workspace-input returnerer `build_prompt(user_text)` protocol-kort,
workspace-snapshot, brukertext og en JSON-only-påminnelse. For kontrollert study-input
returnerer den i stedet study-context og den faste verbatim-responsmarkøren.

**Hvorfor er den bygget slik?**  
Prompting er ikke et andre protocol. Validering skjer fortsatt i `protocol.py`.

v0.4: prompten beskriver `move`/`remove` og inkluderer et kompakt serialisert
workspace-snapshot. Snapshotet inneholder ingen block-content, filstier eller Qt-state.

v0.5: `build_prompt` kan i tillegg få en liten study-context med valgt problem,
interaction-mode, relevant tidligere respons og eksakt tillatt response-slot. En
mode-spesifikk policy begrenser hint, feedback og neste steg; vanlig prompt er uendret.
Ved ordinær generering av en oppgave/problem/task krever protocol-kortet at hovedteksten
bruker stabil id `problem-1`, slik at den kan bli study-target uten semantisk scanning.

Kontrollerte study-turns bruker ikke JSON-output. De får en egen prompt som krever den
faste `SURFACE_STUDY_RESPONSE\ncontent:\n`-markøren etterfulgt av verbatim pedagogisk
tekst. Dermed kan Markdown, Unicode, linjeskift og LaTeX-backslashes returneres uten at
Hermes serialiserer en Surface-command. Vanlige workspace-prompts bruker fortsatt det
strenge JSON-kortet under.

Den ordinære JSON-kontrakten sier eksplisitt at output må kunne parses med Python `json.loads`,
at backslashes og linjeskift i strenger må JSON-escapes, og at rå kontrolltegn er
forbudt. Markdown kan brukes i `content`; Unicode-matematikksymboler foretrekkes
når de unngår usikre backslash-sekvenser.

**Naturlig videre utvikling**
Juster kortet når ekte Hermes-økter viser typiske feil; ikke utvid command-skjemaet for modellens skyld.
