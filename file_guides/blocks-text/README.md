# blocks/text.py

Source: `src/surface/blocks/text.py`

**Hva er ansvaret?**  
Renderer `TextCommand` som plain text eller markdown i en Qt-widget.

**Hvordan går data inn og ut?**  
En `TextCommand` går inn i `render()`; widgetens dokument oppdateres og rapporterer riktig størrelse til layouten.

**Hvorfor er den bygget slik?**  
Tekstrepresentasjonen holdes isolert fra protocol og workspace, slik at rendering kan endres uten å endre command-kontrakten.

**Naturlig videre utvikling**  
Bedre typografi, selection/annotation og eventuelt rikere tekstcapabilities kan bygges her når studiebruk viser behovet.