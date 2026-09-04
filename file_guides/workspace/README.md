# workspace.py

Source: `src/surface/workspace.py`

**Hva er ansvaret?**  
Eier de aktive block-widgetene og holder koblingen mellom command-ID, command-data og renderet widget.

**Hvordan går data inn og ut?**  
`Command` går inn via `upsert`; workspace oppretter eller oppdaterer riktig block og returnerer `created` eller `updated`.

**Hvorfor er den bygget slik?**  
Den samler UI-tilstanden på ett sted og lar dispatcher slippe å kjenne Qt-detaljer.

v0.4: workspace eier én `WorkspaceState`. En command-liste planlegges og valideres
atomisk i den Qt-frie komposisjonsmodulen før eksisterende widgets reparenteres.
`snapshot()` eksponerer bare id, type, parent, index og layout-retning til Hermes.
Fjerning av layout bevarer direkte children ved root.

**Naturlig videre utvikling**  
Komposisjon, plassering og relasjoner mellom blocks hører naturlig hjemme rundt denne delen når Surface går fra vertikal stack til en ekte arbeidsflate.
