# hermes_bridge.py

Source: `src/surface/hermes_bridge.py`

**Hva er ansvaret?**  
Er adapteren mellom rå ekstern tekst/JSON og Surface-protokollen.

**Hvordan går data inn og ut?**  
`from_hermes_output` / `from_user_input` tar kun strukturert JSON (`{`/`[`). Naturlig språk går via `complete(text, transport)` → prompt + transport + valgfri ```json-fence → `from_hermes_output`. Prose blir ikke lenger en lokal `TextCommand`.

**Hvorfor er den bygget slik?**  
Ekstern agentintegrasjon isoleres fra resten av Surface, slik at UI og core ikke trenger å vite hvordan Hermes kommuniserer.

**Naturlig videre utvikling**  
Når Hermes kobles på ekte kan transport, prompting og output-normalisering bygges her eller bak denne grensen uten å endre Surface-protokollen.