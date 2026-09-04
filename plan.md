# Plan — v0.3

## Kort status

v0.1 etablerte Surface-kjernen: native PySide6-vindu, typesikkert command-protocol og rendering av `text`, `equation`, `image` og `plot`.

v0.2 la til komposisjon med `layout`, slik at eksisterende blocks kan organiseres vertikalt og horisontalt med kontrollert ownership, cycle-sjekk og upsert.

## Mål

Koble ekte Hermes til Surface slik at naturlig språk fra brukeren kan oversettes til validerte Surface-kommandoer og endre arbeidsflaten uten at brukeren må skrive JSON eller tekniske kommandoer manuelt.

## Scope

### Skal med i v0.3
- Ekte Hermes-transport bak `hermes_bridge.py`.
- Naturlig språk fra Surface-input skal kunne sendes til Hermes.
- Hermes skal returnere strukturert output som kan normaliseres til eksisterende Surface-protocol.
- Hermes skal kun kunne uttrykke eksisterende command-typer:
  - `text`
  - `equation`
  - `image`
  - `plot`
  - `layout`
- Surface skal fortsatt eie parsing, validering, state, composition og rendering.
- Hermes-output skal alltid gå gjennom eksisterende protocol før dispatch.
- Kontrollert håndtering av:
  - ugyldig JSON
  - ukjent command-type
  - manglende felt
  - ugyldige layout-referanser
  - tom eller ubrukelig Hermes-output
  - transport-/prosessfeil
- Minst noen få representative naturlig-språk-prompts som eval/test.
- Tydelig separasjon mellom transport, prompting/output-normalisering og Surface-core.
- Eksisterende `--inject`/lokal strukturert input skal fortsatt fungere for debugging og tester.

### Skal ikke med i v0.3
- Nye workspace-manipulasjonskommandoer utover eksisterende protocol.
- Fri naturlig språk-styring av flytting, sletting eller restrukturering utover det Hermes kan uttrykke med eksisterende `layout`-commands.
- Memory-system.
- Knowledge graph.
- Learning-loop eller mastery-modell.
- Automatisk pedagogisk planlegging.
- 3D-rendering.
- Voice.
- Multi-agent-system.
- Plugins/MCP.
- Persistente workspaces.
- Ny layoutmotor.
- Visuell design-pass.

## Arkitekturretning

v0.3 skal bevare samme grense som før:

```text
User natural language
        |
        v
Surface input
        |
        v
Hermes Bridge
        |
        +--> Hermes transport
        |       |
        |       v
        |   Hermes / model
        |       |
        |       v
        +<-- raw model output
        |
        v
output normalisation
        |
        v
Surface Protocol
        |
        v
Dispatcher
        |
        v
Workspace / Blocks / Layout
```

Hermes skal ikke kjenne Qt eller manipulere widgets direkte. Den skal kun produsere strukturert intent som Surface kan validere og anvende.

## Viktig kontrakt

`hermes_bridge.py` er adapteren mellom ekstern agent og Surface.

Konseptuelt:

```text
natural language
    -> Hermes request
    -> raw Hermes output
    -> normalised JSON/commands
    -> parse_command_list(...)
    -> list[Command]
```

Surface-core skal ikke være avhengig av hvordan Hermes startes, hvilken modell Hermes bruker eller hvordan transporten er implementert.

## Eksempel på ønsket flyt

Bruker:

```text
Vis bøyspenningsformelen og lag et enkelt momentdiagram ved siden av forklaringen.
```

Hermes kan produsere noe i retning av:

```json
{
  "commands": [
    {
      "type": "text",
      "id": "explanation-1",
      "content": "Bøyspenning beskrives med ..."
    },
    {
      "type": "equation",
      "id": "eq-1",
      "latex": "\\sigma = \\frac{My}{I}"
    },
    {
      "type": "plot",
      "id": "plot-1",
      "series": [
        {"x": [0, 1, 2], "y": [0, 1, 0], "label": "M", "kind": "line"}
      ],
      "title": "Moment along beam",
      "xlabel": "x",
      "ylabel": "M"
    },
    {
      "type": "layout",
      "id": "study-1",
      "direction": "horizontal",
      "children": ["explanation-1", "plot-1"]
    }
  ]
}
```

Det viktige i v0.3 er ikke at output alltid er perfekt pedagogisk, men at naturlig språk kan drive eksisterende Surface-state gjennom en trygg og tydelig kontrakt.

## Designspørsmål som skal avklares i implementasjonsplanen

- Hvilken Hermes-transport er minst kompleks og mest robust for lokal v0.3?
- Skal Hermes kjøres som subprocess, CLI-kall, lokal HTTP-prosess eller gjennom annen eksisterende mekanisme?
- Skal Hermes holdes varm mellom requests, eller kan v0.3 bruke ett kall per input?
- Hvordan instrueres Hermes til å produsere kun gyldige Surface-commands?
- Skal bridge trekke JSON ut av prose/code fences, eller skal ikke-konform output avvises direkte?
- Hvor mye normalisering er akseptabelt før bridge begynner å skjule modellfeil?
- Hvordan skal timeout, prosessfeil og tom output rapporteres til UI uten å blokkere eller krasje vinduet?
- Må Hermes-kallet kjøres utenfor Qt GUI-tråden for å unngå at vinduet fryser?
- Hvordan testes bridge uten å kreve et ekte modellkall i hver test?

## Eval / representative prompts

Minst disse typene skal prøves:

1. Enkel tekst:
   - «Forklar hva gradient betyr kort.»
2. Tekst + ligning:
   - «Vis bøyspenningsformelen og forklar symbolene.»
3. Tekst + plot:
   - «Vis et enkelt trekantformet momentdiagram.»
4. Flere representasjoner + layout:
   - «Vis forklaring og figur/plot ved siden av hverandre.»
5. Uklart eller ikke-renderbart input:
   - Surface skal håndtere resultatet kontrollert uten crash.

## Definition of Done

v0.3 er ferdig når:

- En vanlig naturlig språk-prompt kan skrives i Surface og sendes til ekte Hermes.
- Hermes-output går gjennom `hermes_bridge.py` og eksisterende Surface-protocol før dispatch.
- Minst én prompt oppretter flere ulike representasjoner og én `layout` uten manuell JSON.
- Ugyldig eller ufullstendig Hermes-output gir kontrollert feil og krasjer ikke applikasjonen.
- Hermes-transportfeil eller timeout håndteres kontrollert.
- UI fryser ikke merkbart under normal Hermes-bruk.
- Eksisterende primitive commands, `layout`, `--inject` og v0.2-tester fortsetter å fungere.
- Bridge-/transportlogikk kan testes uten ekte modellkall gjennom fake/mock transport.
- Det er ikke lagt til nye command-typer eller workspace-manipulasjon bare for å gjøre Hermes enklere å bruke.

## Designprinsipper

- Hermes uttrykker intent; Surface eier state og rendering.
- All modell-output behandles som uvalidert ekstern input.
- Eksisterende protocol er kontrakten; v0.3 skal primært integrere, ikke redesigne den.
- Hold transport utskiftbar og isolert fra core.
- Ikke skjul modellfeil med aggressiv parsing eller heuristikker.
- Preferer eksplisitt strukturert output fremfor teknisk naturlig språk som må tolkes senere.
- Bygg akkurat nok agentintegrasjon til å gjøre Surface naturlig å bruke.
- Generaliser etter observerte behov, ikke før.
