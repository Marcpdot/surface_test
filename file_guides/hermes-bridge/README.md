# hermes_bridge.py

Source: `src/surface/hermes_bridge.py`

**Hva er ansvaret?**  
Er adapteren mellom rå ekstern tekst/JSON og Surface-protokollen.

**Hvordan går data inn og ut?**  
`from_hermes_output` / `from_user_input` tar kun strukturert JSON (`{`/`[`). Naturlig språk går via `complete(text, transport)` → prompt + transport + valgfri hel-streng ```json-fence → `from_hermes_output`. Prose blir ikke lenger en lokal `TextCommand`. Ved `cannot_translate` (og andre parse-feil etter transport) logges rå Hermes-stdout; UI-meldingen tar med en kort preview. Ingen JSON-fisking i prosa.

**Hvorfor er den bygget slik?**  
Ekstern agentintegrasjon isoleres fra resten av Surface, slik at UI og core ikke trenger å vite hvordan Hermes kommuniserer.

v0.4: `complete` mottar det semantiske workspace-snapshotet og gir det videre til
promptbyggeren. Parsing og transport er ellers uendret.

v0.5: `complete` kan motta en separat study-context. Broen transporterer og parser
fortsatt bare Surface-commands; study-policy og session-state eies ikke her.

Ved `invalid_json` logger broen `JSONDecodeError`-melding, linje, kolonne og
tegnposisjon før den eksisterende rå-stdout-diagnostikken. Output blir fortsatt
avvist direkte; broen forsøker ingen JSON-reparasjon.

**Naturlig videre utvikling**
Når Hermes kobles på ekte kan transport, prompting og output-normalisering bygges her eller bak denne grensen uten å endre Surface-protokollen.
