# blocks/__init__.py

Source: `src/surface/blocks/__init__.py`

**Hva er ansvaret?**  
Mapper `command.type` til riktig konkret `Block`-klasse og oppretter widgeten.

**Hvordan går data inn og ut?**  
En typed `Command` går inn i `create_block`; en konkret `TextBlock`, `EquationBlock`, `ImageBlock` eller `PlotBlock` kommer ut.

**Hvorfor er den bygget slik?**  
Factory-grensen gjør at workspace slipper å inneholde en stor kjede med type-spesifikk konstruksjonslogikk.

**Naturlig videre utvikling**  
Hvis antallet representasjoner blir stort kan factory-tabellen utvikles til et registry, men dagens eksplisitte mapping er riktig for prototypen.