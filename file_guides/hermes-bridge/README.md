# hermes_bridge.py

Source: `src/surface/hermes_bridge.py`

**Hva er ansvaret?**  
Er adapteren mellom rå ekstern tekst/JSON og Surface-protokollen.

**Hvordan går data inn og ut?**  
`from_hermes_output` / `from_user_input` tar kun strukturert JSON (`{`/`[`). Naturlig
språk går via `complete(text, transport)`. Ordinære svar bruker den strenge JSON-veien;
kontrollerte study-svar bruker bare den faste study-markøren. Ved parse-feil etter
transport logges rå Hermes-stdout. Ingen JSON-fisking eller generell reparasjon i prosa.

**Hvorfor er den bygget slik?**  
Ekstern agentintegrasjon isoleres fra resten av Surface, slik at UI og core ikke trenger å vite hvordan Hermes kommuniserer.

v0.4: `complete` mottar det semantiske workspace-snapshotet og gir det videre til
promptbyggeren. Parsing og transport er ellers uendret.

v0.5: `complete` kan motta en separat study-context. Vanlige Hermes-svar går fortsatt
strengt gjennom `parse_command_list`/`json.loads`. For en kontrollert study-turn godtar
broen bare den eksakte `SURFACE_STUDY_RESPONSE\ncontent:\n`-markøren og behandler resten
som verbatim tekst. Response-id og lengdegrense hentes fra Surface sin study-context;
Hermes kan ikke velge type eller id. Den ferdige `TextCommand` valideres fortsatt mot
den aktuelle `StudyTurn` i `StudySession.finalize`.

Ved `invalid_json` logger broen `JSONDecodeError`-melding, linje, kolonne og
tegnposisjon før den eksisterende rå-stdout-diagnostikken. Output blir fortsatt
avvist direkte; broen forsøker ingen JSON-reparasjon.

**Naturlig videre utvikling**
Når Hermes kobles på ekte kan transport, prompting og output-normalisering bygges her eller bak denne grensen uten å endre Surface-protokollen.
