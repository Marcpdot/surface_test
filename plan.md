# Plan — v0.5

## Mål

Gjør Surface i stand til å støtte en enkel, interaktiv study-loop på et eksisterende workspace, slik at Hermes kan gi hint, be om brukerforsøk, gi kontrollert feedback og gå videre stegvis uten å avsløre hele løsningen med mindre brukeren ber om det.

## Scope

### Skal med i v0.5
- En liten, eksplisitt study-interaction-modell over eksisterende workspace og Hermes-integrasjon.
- Minst denne flyten:
  1. oppgave/problem finnes allerede i workspace
  2. bruker ber om hjelp eller forsøker et svar
  3. Hermes gir neste pedagogiske respons
  4. Surface oppdaterer workspace kontrollert
  5. løsningen kan holdes tilbake eller vises stegvis
- Brukeren skal kunne be om:
  - kun et hint
  - ett neste steg
  - kort feedback på eget forsøk
  - ny variant av samme type oppgave
  - å fortsette eller avsløre løsningen eksplisitt
- Hermes skal bruke eksisterende workspace-snapshot og stabile IDs for å oppdatere relevante blocks i stedet for å bygge hele flaten på nytt.
- Study-respons skal fortsatt uttrykkes gjennom Surface-protokollen og eksisterende workspace-operasjoner.
- Minst én enkel study-state eller interaction-context som forteller Hermes hva slags hjelp som er ønsket i den aktuelle runden.
- Kontrollert håndtering av uklare eller uegnede study-requests uten crash eller uønsket full løsning.
- Tester for study-routing, prompt/context og at eksisterende workspace-state ikke korrumperes.
- En manuell demonstrasjon der en oppgave brukes gjennom flere runder, for eksempel:
  - «gi meg bare et hint»
  - bruker svarer
  - Hermes gir feedback
  - «vis neste steg»

### Skal ikke med i v0.5
- Automatisk import eller parsing av ekte bok-/øvingsoppgaver.
- PDF-, bilde- eller OCR-ingestion.
- Full mastery-modell eller knowledge tracing.
- Langtidsminne mellom study sessions.
- Automatisk pensumplanlegging.
- Knowledge graph.
- 3D-rendering.
- Voice.
- Multi-agent-system.
- Plugins/MCP.
- Persistente workspaces.
- Ny layoutmotor.
- Fri canvas/docking.
- Ferdig visuell design.

## Arkitekturretning

v0.5 skal bygge på det som allerede finnes:

```text
Workspace state
     |
     v
Workspace snapshot
     |
     v
User study request / attempt
     |
     v
Study interaction context
     |
     v
Hermes
     |
     v
Surface commands
     |
     v
Atomic protocol + workspace update
```

Study-laget skal ikke eie rendering eller Qt-state. Det skal kun beskrive pedagogisk intensjon og kontekst rundt den neste Hermes-responsen.

## Study interaction

v0.5 trenger ikke et fullverdig pedagogisk system. Målet er å bevise én liten feedback-loop:

```text
Problem
  -> Hint
  -> User attempt
  -> Feedback
  -> Next hint/step
  -> ...
```

Surface skal kunne skille mellom ulike intensjoner, for eksempel:

```text
hint_only
next_step
check_attempt
show_solution
new_variant
```

Eksakt representasjon avgjøres i implementasjonsplanen. Det viktige er at study-intensjon er eksplisitt nok til at Hermes ikke automatisk løser alt.

## Viktig designregel: ikke avslør mer enn forespurt

Når brukeren ber om hint eller feedback skal systemet instruere Hermes til å begrense responsen til akkurat det nivået.

Eksempel:

Bruker:

```text
Gi meg bare et hint.
```

Ønsket respons kan være:

```text
- én kort retning eller påminnelse
- eventuell relevant ligning dersom nødvendig
- ingen full utregning
- ingen fasit
```

Bruker:

```text
Jeg fikk 60 MPa. Er det riktig?
```

Ønsket respons:

```text
- vurder forsøket
- forklar kort hva som er riktig/feil
- gi neste korrigerende hint ved behov
- ikke løs resten automatisk
```

## Workspace-bruk

v0.5 skal bruke v0.4-manipulasjonen i stedet for å lage en separat study-UI.

Konseptuelt kan workspace bestå av eksisterende blocks som:

```text
problem-1
attempt-1
hint-1
feedback-1
step-1
solution-1
```

Hermes kan opprette eller oppdatere disse gjennom eksisterende `text`, `equation`, `plot`, `layout`, `move` og `remove`-commands.

Det skal ikke innføres spesialiserte Qt-widgets for «hint», «feedback» eller «solution» i v0.5 med mindre implementasjonsdesignet viser et konkret behov.

## Study context til Hermes

Hermes trenger mer enn bare workspace-struktur i v0.5. Implementasjonsplanen skal definere det minste ekstra contextet som trengs for study-loop, for eksempel:

```json
{
  "study": {
    "mode": "hint_only",
    "user_message": "Jeg skjønner ikke hvordan jeg starter.",
    "target_id": "problem-1"
  }
}
```

Dette skal være kort, serialiserbart og eksplisitt.

Det skal ikke utvikles til et fullverdig learner-profile eller mastery-system i v0.5.

## Designspørsmål som skal avklares i implementasjonsplanen

- Skal study-intensjon være en intern enum/dataclass eller en ny Surface-command?
- Hvordan skilles et vanlig natural-language workspace-request fra et study-request?
- Trenger Hermes problem-content i prompten, eller er workspace-snapshot uten content for lite for study-feedback?
- Hvis content må inkluderes: hva er minste sikre og relevante study-context som kan sendes uten å gjøre snapshotet til en full workspace-dump?
- Hvordan refererer brukeren til eget forsøk og riktig problem/block pålitelig?
- Skal attempts lagres som vanlige `text`-blocks eller bare sendes som request-context?
- Hvordan sikrer vi at `hint_only` faktisk ikke resulterer i full løsning?
- Hvordan bør «new_variant» fungere uten å introdusere en task-ingestion/task-model allerede nå?
- Hvordan håndteres en study-request som ikke passer til innholdet i workspace?
- Trenger vi en enkel session-state i Surface, eller kan v0.5 være stateless mellom hver request utover eksisterende workspace?

## Representative study-scenarier

Minst disse skal fungere:

1. «Gi meg bare et hint til denne oppgaven.»
2. «Vis ett neste steg, men ikke løs resten.»
3. «Jeg fikk 60 MPa. Er det riktig?»
4. «Hvor gjorde jeg feil?»
5. «Lag en ny variant med andre tall.»
6. «Nå kan du vise hele løsningen.»
7. Uklart study-request skal håndteres kontrollert uten at hele løsningen genereres automatisk.

## Definition of Done

v0.5 er ferdig når:

- En eksisterende oppgave i workspace kan brukes gjennom minst tre study-runder uten å bygge flaten på nytt.
- Brukeren kan be om et hint uten at full løsning vises.
- Brukeren kan sende et eget forsøk og få begrenset, relevant feedback.
- Brukeren kan be om ett neste steg og få workspace oppdatert med bare dette steget.
- Full løsning vises først når brukeren eksplisitt ber om det i den validerte demo-flowen.
- Hermes kan bruke eksisterende workspace-IDs og study-context til å oppdatere relevante blocks.
- v0.4 atomisk workspace-manipulasjon brukes fortsatt for alle workspace-endringer.
- Study-interaction kan testes med fake/mock Hermes uten ekte modellkall.
- Feil eller uklare study-requests håndteres kontrollert uten state-korrupsjon eller crash.
- Eksisterende v0.1–v0.4-funksjonalitet fortsetter å fungere.
- Det er ikke introdusert full mastery-tracking, oppgaveimport, generell pedagogisk planner eller nye UI-abstraksjoner uten konkret behov.

## Designprinsipper

- Study-loop først, learning-platform senere.
- Ikke avslør mer enn brukeren ber om.
- Hermes uttrykker pedagogisk respons; Surface eier state, validering og rendering.
- Bruk eksisterende representasjoner og workspace-operasjoner før nye abstraheringer introduseres.
- Hold study-context lite og eksplisitt.
- Ikke bygg mastery/learner model før faktiske study-sessions viser behovet.
- Bruk ekte study-interaksjoner som feedback på hva v0.6 bør bli.
- Ekte bok-/øvingsoppgave-ingestion flyttes til en senere versjon.
