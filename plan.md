# Plan — v0.2

## Kort status fra v0.1

v0.1 etablerte en borderless native PySide6-Surface med et typesikkert command-protocol for `text`, `equation`, `image` og `plot`, samt dispatcher, workspace, rendering, input og kontrollert feilhåndtering. Dette er nå grunnlaget v0.2 bygger videre på.

## Mål

Bygg komposisjon av representasjoner slik at eksisterende blocks kan organiseres sammen i en arbeidsflate med meningsfulle relasjoner, i stedet for kun å vises som en vertikal stabel.

## Scope

### Skal med i v0.2
- Et lite, eksplisitt layout-/composition-språk for å organisere eksisterende blocks.
- Minst to enkle komposisjonsformer:
  - vertikal
  - horisontal/split
- Mulighet til å gruppere flere eksisterende block-id-er i én komposisjon.
- Rekursiv eller nestbar struktur dersom dette kan gjøres uten unødvendig kompleksitet.
- Surface skal eie hvordan layout faktisk rendres; eksterne produsenter skal kun uttrykke struktur/intensjon.
- Eksisterende `text`, `equation`, `image` og `plot` skal kunne brukes uendret inni komposisjoner.
- Kontrollert håndtering av ugyldige referanser, duplikater eller ugyldig layoutstruktur.
- Tester for parsing/validering av composition-protocol og routing til workspace.
- En demo som viser minst én reell studie-lignende komposisjon, for eksempel tekst + figur ved siden av hverandre og ligning + plot under.

### Skal ikke med i v0.2
- Ekte Hermes-/LLM-integrasjon.
- Automatisk AI-generert layout.
- Memory-system.
- Knowledge graph.
- Learning-loop eller mastery-modell.
- 3D-rendering.
- Voice.
- Multi-agent-system.
- Plugins/MCP.
- Fri canvas med vilkårlig dragging/positionering.
- Fullverdig docking/window manager.
- Ferdig visuell design.
- Persistente workspaces.

## Arkitekturretning

v0.1 har primitive representasjoner:

```text
TextBlock
EquationBlock
ImageBlock
PlotBlock
```

v0.2 introduserer komposisjon over disse:

```text
Representation
├── Primitive
│   ├── TextBlock
│   ├── EquationBlock
│   ├── ImageBlock
│   └── PlotBlock
└── Composition
    ├── Vertical
    └── Horizontal / Split
```

Målet er at Surface kan uttrykke noe i retning av:

```text
Horizontal
├── TextBlock(problem)
└── ImageBlock(figure)

Vertical
├── Horizontal(problem, figure)
└── Horizontal(equation, plot)
```

Komposisjon skal beskrive relasjonen mellom representasjonene, ikke innholdet i dem.

## Protocol-retning

Composition bør bygges som en liten utvidelse av det eksisterende command-språket, ikke som en separat UI-API.

Konseptuelt eksempel:

```json
{
  "type": "layout",
  "id": "study-1",
  "direction": "horizontal",
  "children": ["problem-1", "figure-1"]
}
```

En nestet variant kan senere være:

```json
{
  "type": "layout",
  "id": "study-1",
  "direction": "vertical",
  "children": [
    {
      "direction": "horizontal",
      "children": ["problem-1", "figure-1"]
    },
    {
      "direction": "horizontal",
      "children": ["equation-1", "plot-1"]
    }
  ]
}
```

Eksakt schema skal avgjøres i implementasjonsdesignet. Det viktige er at formatet er lite, eksplisitt, validerbart og enkelt å utvide senere.

## Designspørsmål som skal avklares i implementasjonsplanen

- Skal `layout` være en ny `Command`-type eller en separat komposisjonsnode over eksisterende commands?
- Skal children kun være block-id-er i v0.2, eller skal nesting støttes direkte?
- Hvordan skal ownership fungere når en block flyttes inn i en komposisjon?
- Skal samme block kunne eksistere i flere komposisjoner samtidig, eller må én block ha én visuell forelder?
- Hvordan skal oppdatering av en eksisterende layout fungere med samme `id`?
- Hvordan skal ugyldige eller manglende child-referanser håndteres uten å krasje UI-et?
- Hvordan unngår vi at layout-protocolen blir en generell UI-beskrivelse av Qt-widgets?

## Definition of Done

v0.2 er ferdig når:

- Eksisterende primitive blocks fortsatt fungerer som i v0.1.
- Surface kan opprette minst én vertikal og én horisontal komposisjon gjennom strukturert input.
- Flere eksisterende representasjoner kan organiseres i én meningsfull studie-lignende arbeidsflate.
- En komposisjon kan oppdateres kontrollert uten å duplisere eller miste blocks.
- Ugyldige layout-kommandoer avvises kontrollert uten at applikasjonen krasjer.
- Composition-protocol og routing har automatiserte tester.
- Demoen viser at layouten faktisk gjør Surface mer nyttig enn den rene vertikale stabelen fra v0.1.
- Det er ikke introdusert en generell layoutmotor eller abstraheringer som ikke er nødvendige for disse konkrete behovene.

## Designprinsipper

- Komposisjon beskriver relasjoner mellom representasjoner; Surface bestemmer konkret rendering.
- Behold eksisterende primitive blocks enkle og uavhengige.
- Foretrekk noen få komponerbare primitives fremfor mange spesialiserte layouts.
- Unngå å modellere hele Qt-widget-treet i protocolen.
- Bruk en rekursiv struktur bare dersom den faktisk gjør implementasjonen enklere og mer uttrykksfull.
- Generaliser etter observerte behov, ikke før.
- Målbar nytte kommer før arkitektonisk kompleksitet.
