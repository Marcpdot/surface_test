# window.py

Source: `src/surface/window.py`

**Hva er ansvaret?**  
Eier hovedvinduet, brukerinput, statusvisning og koblingen mellom bridge, dispatcher og workspace.

**Hvordan går data inn og ut?**  
JSON og `--inject`/`--demo` parses synkront. Naturlig språk kjører `HermesBridge.complete` på en `QThread` (subprocess aldri på GUI-tråden). Status `waiting…` mens kallet pågår; `ProtocolError` vises på statuslinjen.

v0.4: window tar et workspace-snapshot på GUI-tråden før Hermes-worker startes, og
alle returnerte command-lister anvendes atomisk. Manuell smoke: åpne `--demo`, send
«Flytt ligningen før plottet i modellraden», og kontroller at eksisterende blocks flyttes.

**Hvorfor er den bygget slik?**  
Den fungerer som Qt-grensen der UI-events møter den Qt-frie kjernen.

**Naturlig videre utvikling**  
Når interaction-logikken blir større bør session/controller-ansvar trekkes ut, mens window fortsatt primært eier native vindu og brukerhendelser.
