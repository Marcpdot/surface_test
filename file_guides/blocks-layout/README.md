# blocks/layout.py

Source: `src/surface/blocks/layout.py`

**Hva er ansvaret?**  
Renderer en `LayoutCommand` som vertikal eller horisontal `QBoxLayout` og tar imot child-widgets fra workspace.

**Hvordan går data inn og ut?**  
`render()` setter retning. `set_children()` plasserer eksisterende block-widgets i den rekkefølgen protocolen oppgir. Surface eier stretch (lik andel).

**Hvorfor er den bygget slik?**  
Protocolen beskriver bare relasjon (v/h + id-er). Widget-treet forblir Qts ansvar.

**Naturlig videre utvikling**  
Ikke flere layout-typer før et konkret studiebehov viser at v/h ikke holder.
