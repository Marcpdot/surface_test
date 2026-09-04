# study.py

Source: `src/surface/study.py`

**Hva er ansvaret?**  
Qt-fri routing og minimal session-state for v0.5 study-loop. Modulen skiller hint,
neste steg, forsøk/feedback, eksplisitt løsning og ny variant.

**Hvordan går data inn og ut?**  
`StudySession.prepare` gjør brukerens tekst og eksisterende text-blocks om til en
immutable `StudyTurn` eller returnerer `None` for vanlig workspace-input.
`finalize` validerer Hermes-commands mot turnens ene tillatte response-slot og lager
eventuelle deterministiske attempt-/cleanup-commands. `commit` kalles først etter en
vellykket atomisk workspace-dispatch.

**Hvorfor er den bygget slik?**  
Pedagogisk innhold kommer fra Hermes, mens Surface deterministisk eier intent,
disclosure-grense, stabile IDs og state-overganger. Dette gjør study-loop testbar uten
Qt eller ekte modellkall og hindrer at all kontroll skjules i fri prompttekst.

**Avgrensning**  
Ingen mastery-modell, historisk minne, task-ingestion eller pedagogisk planner.
Eksplisitt negerte løsningsfraser fjernes før solution-intent vurderes, slik at vanlige
opprettingsrequests som «lag en oppgave, men ikke løs den» går til ordinær Hermes-flow.
