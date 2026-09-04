# hermes_prompt.py

Source: `src/surface/hermes_prompt.py`

**Hva er ansvaret?**  
Statisk protocol-kort som forteller Hermes hvilke command-typer og felt som er gyldige.

**Hvordan går data inn og ut?**  
`build_prompt(user_text)` returnerer kort + `User:` + teksten. Ingen historikk, ingen workspace-dump.

**Hvorfor er den bygget slik?**  
Prompting er ikke et andre protocol. Validering skjer fortsatt i `protocol.py`.

**Naturlig videre utvikling**  
Juster kortet når ekte Hermes-økter viser typiske feil; ikke utvid command-skjemaet for modellens skyld.
