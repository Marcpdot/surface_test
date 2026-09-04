# Plan — v0.4

## Mål

Gjør Surface i stand til å manipulere eksisterende workspace-state kontrollert gjennom eksplisitte commands, slik at Hermes kan endre en allerede oppbygd arbeidsflate i stedet for bare å legge til nytt innhold.

## Scope

### Skal med i v0.4
- Et lite, eksplisitt workspace-manipulasjonsspråk over eksisterende blocks og layouts.
- Mulighet til å oppdatere eksisterende block-innhold via eksisterende upsert-by-id.
- Mulighet til å endre struktur i workspace uten å måtte bygge hele flaten på nytt.
- Minst disse manipulasjonene:
  - flytte/reparent en eksisterende block eller layout til en annen layout
  - endre rekkefølge på children i en layout
  - flytte en block tilbake til root
  - fjerne en block eller layout kontrollert
- Layout- og ownership-regler skal fortsatt være eksplisitte og validerte.
- Ugyldige manipulasjoner skal avvises uten delvis mutasjon av workspace.
- Hermes skal kunne uttrykke manipulasjoner gjennom Surface-protokollen, men Surface skal fortsatt eie state, validering og konkret Qt-manipulasjon.
- Eksisterende `text`, `equation`, `image`, `plot` og `layout` skal fortsette å fungere som før.
- Tester for alle nye workspace-operasjoner og deres feilhåndtering.
- En demo eller manuell test som viser at en eksisterende studieflate kan reorganiseres gjennom en ny naturlig språk-prompt uten å opprette alt på nytt.

### Skal ikke med i v0.4
- Automatisk import eller parsing av ekte bok-/øvingsoppgaver.
- PDF-, bilde- eller OCR-ingestion.
- Memory-system.
- Knowledge graph.
- Learning-loop eller mastery-modell.
- Automatisk pedagogisk planlegging.
- 3D-rendering.
- Voice.
- Multi-agent-system.
- Plugins/MCP.
- Persistente workspaces.
- Fri canvas med vilkårlig dragging.
- Full docking/window manager.
- Ny generell layoutmotor.
- Ferdig visuell design.

## Arkitekturretning

v0.4 skal utvide den eksisterende command-kontrakten med noen få eksplisitte workspace-operasjoner, ikke introdusere en separat Qt- eller widget-API.

Konseptuelt:

```text
User natural language
        |
        v
Hermes
        |
        v
Surface command(s)
        |
        v
Protocol validation
        |
        v
Workspace operation
        |
        v
Existing workspace state changes
```

Hermes skal fortsatt ikke manipulere widgets direkte. Den skal kun uttrykke ønsket state-endring gjennom validerte commands.

## Manipulasjonsmodell

v0.4 skal bygge videre på eksisterende identitet og ownership:

- alle blocks/layouts har stabile `id`
- én visuell parent per node
- root er gyldig parent
- layouts eier rekkefølgen på sine children
- primitive upserts oppdaterer innhold uten å endre plassering

Nye operasjoner bør være små og ortogonale.

Konseptuelle eksempler:

```json
{
  "type": "move",
  "id": "eq-1",
  "parent": "row-model",
  "index": 0
}
```

```json
{
  "type": "move",
  "id": "plot-1",
  "parent": null
}
```

```json
{
  "type": "remove",
  "id": "hint-1"
}
```

Eksakt schema skal avgjøres i implementasjonsplanen. Det viktige er at operasjonene er eksplisitte, validerbare og enkle å anvende atomisk.

## Designspørsmål som skal avklares i implementasjonsplanen

- Skal `move` og `remove` være egne command-typer, eller bør layout-upsert alene uttrykke deler av dette?
- Trenger vi en egen `reorder`-kommando, eller kan `move(..., index=...)` dekke behovet?
- Hvordan representeres root som parent på en eksplisitt måte?
- Hvilke regler gjelder når en layout fjernes: skal children returnere til root eller fjernes rekursivt?
- Hvordan skal `remove` av en block som brukes i en layout håndteres?
- Hvordan sikrer vi at en sekvens av manipulasjonskommandoer ikke etterlater workspace i delvis mutert state ved feil?
- Skal flere operasjoner i én Hermes-response anvendes sekvensielt som i dag, eller trenger enkelte workspace-endringer en liten atomisk batch-grense?
- Hvordan skal Hermes få nok kunnskap om eksisterende workspace-id-er og struktur til å referere til dem korrekt, uten å sende hele Qt-state?
- Hva er minste workspace-snapshot som må gis til Hermes for presis manipulasjon?
- Hvordan unngår vi at protokollen utvikler seg til et generelt imperative UI-språk?

## Viktig nytt behov: workspace context til Hermes

For første gang må Hermes kunne referere til eksisterende state på en pålitelig måte.

v0.4 skal derfor definere en liten, serialiserbar workspace-beskrivelse som kan gis til Hermes, for eksempel:

```json
{
  "nodes": [
    {"id": "problem-1", "type": "text", "parent": "row-1"},
    {"id": "figure-1", "type": "image", "parent": "row-1"},
    {"id": "row-1", "type": "layout", "direction": "horizontal", "parent": "study-1"},
    {"id": "study-1", "type": "layout", "direction": "vertical", "parent": null}
  ]
}
```

Dette skal være Surface-state, ikke Qt-state. Ingen widget-geometri, styling eller interne Qt-objekter skal eksponeres.

## Representative manipulasjoner

Minst disse scenariene skal fungere:

1. «Flytt ligningen ved siden av plottet.»
2. «Legg forklaringen over figuren.»
3. «Flytt plottet tilbake ut av gruppen.»
4. «Bytt rekkefølge på ligningen og plottet.»
5. «Fjern hintet.»
6. «Oppdater forklaringen, men behold plasseringen.»
7. Ugyldig id, cycle eller allerede ugyldig parent skal avvises kontrollert uten state-korrupsjon.

## Definition of Done

v0.4 er ferdig når:

- En eksisterende workspace kan manipuleres uten å bygge hele flaten på nytt.
- Surface støtter kontrollert flytting/reparenting av eksisterende blocks/layouts.
- Surface støtter kontrollert endring av rekkefølge i layout.
- En node kan flyttes tilbake til root.
- En node kan fjernes med tydelig og dokumentert semantikk.
- Primitive upserts fortsetter å oppdatere innhold på stedet uten å endre plassering.
- Ugyldige manipulasjoner avvises uten delvis mutasjon eller tap/duplisering av blocks.
- Hermes kan referere til eksisterende workspace-id-er gjennom en liten serialisert workspace-beskrivelse, uten tilgang til Qt-state.
- Minst én naturlig språk-prompt endrer strukturen på en allerede eksisterende studieflate.
- Alle nye workspace-operasjoner har automatiserte tester.
- Eksisterende v0.1–v0.3-funksjonalitet fortsetter å fungere.
- Det er ikke introdusert en generell UI-layoutmotor eller imperative widget-kontroller.

## Designprinsipper

- Surface eier state; Hermes uttrykker bare ønsket state-endring.
- Identitet (`id`) er grunnlaget for all manipulasjon.
- Workspace-context til Hermes skal beskrive semantisk state, ikke Qt-internals.
- Nye operasjoner skal være få, eksplisitte og ortogonale.
- Foretrekk deklarative state-endringer fremfor tekniske UI-instruksjoner.
- Ingen delvis mutasjon ved avviste commands.
- Behold én visuell parent per node.
- Ikke generaliser til fri canvas eller generell widget-kontroll før konkrete behov krever det.
- v0.4 skal kun bygge infrastrukturen som trengs for at en senere versjon kan sette opp og videreutvikle ekte oppgaver på Surface.
