# Plan — v0.1

## Mål

Bygg en borderless PySide6-arbeidsflate som kan vise tekst, LaTeX/ligninger, bilder og plots, og som kan motta strukturerte kommandoer fra Hermes.

## Scope

### Skal med i v0.1
- Borderless native PySide6-vindu.
- Enkel workspace-flate uten fast chatbot-layout.
- Rendering av tekst/markdown.
- Rendering av LaTeX/ligninger.
- Rendering av bilder.
- Rendering av plots.
- Tekstinput fra bruker.
- Et lite, tydelig strukturert kommandoformat.
- Dispatcher som validerer og sender kommandoer til riktig renderer/block.
- Enkel Hermes-bro som kan oversette Hermes-output til samme kommandoformat.
- Kontrollerte feil ved ugyldige eller ukjente kommandoer.
- Tester for protokoll og dispatcher.

### Skal ikke med i v0.1
- Memory-system.
- Knowledge graph.
- Learning-loop eller mastery-modell.
- 3D-rendering.
- Voice.
- Multi-agent-system.
- Plugins/MCP.
- Kompleks layoutmotor.
- Ferdig visuell design.
- Persistente workspaces.

## Arkitektur

```text
User
  |
  v
PySide6 Surface
  |
  +--> Workspace
  |      |
  |      +--> TextBlock
  |      +--> EquationBlock
  |      +--> ImageBlock
  |      +--> PlotBlock
  |
  +<-- Dispatcher <-- Protocol <-- Hermes Bridge
```

Prinsippet er at Hermes og andre fremtidige komponenter uttrykker intensjon/data gjennom et lite strukturert protocol. Surface bestemmer hvordan dette rendres. AI-laget skal ikke eie UI-presentasjonen.

## Første protocol

Eksempel:

```json
{
  "type": "equation",
  "id": "eq-1",
  "latex": "\\sigma = \\frac{My}{I}"
}
```

Foreløpige command-typer:

- `text`
- `equation`
- `image`
- `plot`

Protocol skal være lite, eksplisitt og enkelt å utvide. Nye command-typer legges kun til når et faktisk behov oppstår.

## Filstruktur

```text
surface/
├── plan.md
├── pyproject.toml
├── src/
│   └── surface/
│       ├── __init__.py
│       ├── app.py
│       ├── window.py
│       ├── workspace.py
│       ├── protocol.py
│       ├── dispatcher.py
│       ├── hermes_bridge.py
│       └── blocks/
│           ├── __init__.py
│           ├── base.py
│           ├── text.py
│           ├── equation.py
│           ├── image.py
│           └── plot.py
└── tests/
    ├── test_protocol.py
    └── test_dispatcher.py
```

## Hva hver fil gjør

- `plan.md` — inneholder kun planen for den aktive versjonen og erstattes/oppdateres når neste versjon planlegges.
- `pyproject.toml` — definerer prosjektmetadata, Python-versjon, dependencies og utviklingsverktøy.
- `src/surface/__init__.py` — markerer `surface` som Python-pakke og eksponerer kun eventuelle bevisst valgte offentlige symboler.
- `src/surface/app.py` — inneholder applikasjonens entry point og oppretter Qt-applikasjonen samt hovedvinduet.
- `src/surface/window.py` — definerer det borderless native hovedvinduet og window-level oppførsel.
- `src/surface/workspace.py` — eier den dynamiske arbeidsflaten og plassering/livssyklus for renderbare blocks.
- `src/surface/protocol.py` — definerer og validerer de strukturerte kommandoene som surface kan motta.
- `src/surface/dispatcher.py` — oversetter validerte kommandoer til konkrete handlinger på workspace og riktige block-typer.
- `src/surface/hermes_bridge.py` — isolerer integrasjonen mot Hermes og konverterer Hermes-output til surface-protokollen.
- `src/surface/blocks/__init__.py` — markerer `blocks` som pakke og kan eksponere de støttede block-typene.
- `src/surface/blocks/base.py` — definerer minimal felles kontrakt for alle renderbare blocks.
- `src/surface/blocks/text.py` — renderer tekst og enkel markdown.
- `src/surface/blocks/equation.py` — renderer LaTeX/matematiske uttrykk.
- `src/surface/blocks/image.py` — renderer lokale eller innlastede bilder.
- `src/surface/blocks/plot.py` — renderer plots fra strukturerte plot-data.
- `tests/test_protocol.py` — tester parsing, validering og kontrollert avvisning av ugyldige kommandoer.
- `tests/test_dispatcher.py` — tester at gyldige kommandoer rutes til riktig workspace/block-handling.

## Implementasjonsrekkefølge

1. Opprett prosjektstruktur og `pyproject.toml`.
2. Lag minimal PySide6-app som åpner et borderless vindu.
3. Implementer `protocol.py` med én command-type: `text`.
4. Implementer `base.py`, `text.py`, `workspace.py` og `dispatcher.py`.
5. Verifiser at et lokalt testkall kan vise tekst gjennom hele kjeden.
6. Legg til `equation`.
7. Legg til `image`.
8. Legg til `plot`.
9. Legg til brukerens tekstinput.
10. Implementer minimal `hermes_bridge.py`.
11. Koble Hermes til protocol i stedet for direkte til UI.
12. Legg til og kjør protocol-/dispatcher-tester.
13. Bruk prototypen i en ekte studieøkt og noter hvilke capabilities som faktisk mangler.

## Definition of Done

v0.1 er ferdig når:

- Applikasjonen starter som et borderless PySide6-vindu.
- Workspace kan vise tekst, én LaTeX-ligning, et bilde og et plot.
- Alle fire representasjoner kan opprettes gjennom samme strukturerte protocol.
- Hermes kan sende minst én gyldig kommando gjennom `hermes_bridge.py` og få den rendret.
- Ugyldige kommandoer avvises kontrollert uten at applikasjonen krasjer.
- Protocol og dispatcher har automatiserte tester.
- Prototypen har blitt brukt i minst én ekte studieøkt.
- Ingen funksjoner utenfor v0.1-scope er lagt til bare fordi de kan være nyttige senere.

## Designprinsipper

- Bygg kun capabilities som et konkret behov krever.
- Hold AI-/agentlogikk adskilt fra presentasjonslaget.
- Foretrekk små, tydelige abstraheringer fremfor generell infrastruktur.
- Bruk Python der rask iterasjon og scientific tooling er viktig; bruk andre språk senere der konkrete ytelses- eller hardwarekrav forsvarer det.
- Matematiske og deterministiske modeller skal brukes der de er bedre egnet enn heuristikker eller LLM-resonnering.
- Målbar nytte kommer før arkitektonisk kompleksitet.
