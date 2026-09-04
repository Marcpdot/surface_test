# workspace.py

Source: `src/surface/workspace.py`

**Hva er ansvaret?**  
Eier de aktive block-widgetene og holder koblingen mellom command-ID, command-data og renderet widget.

**Hvordan går data inn og ut?**  
`Command` går inn via `upsert`; workspace oppretter eller oppdaterer riktig block og returnerer `created` eller `updated`.

**Hvorfor er den bygget slik?**  
Den samler UI-tilstanden på ett sted og lar dispatcher slippe å kjenne Qt-detaljer.

v0.2: workspace holder `_parent_of` (én visuell forelder). Layout-upsert reparenter child-widgets inn i `LayoutBlock` og legger dropp-ede barn tilbake på rot-stakken. `remove` er uendret utover å rydde parent-pekeren for den slettede id-en.

**Naturlig videre utvikling**  
Komposisjon, plassering og relasjoner mellom blocks hører naturlig hjemme rundt denne delen når Surface går fra vertikal stack til en ekte arbeidsflate.