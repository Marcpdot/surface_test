# composition.py

Source: `src/surface/composition.py`

**Hva er ansvaret?**  
Qt-frie v0.2 apply-sjekker: ukjent child, allerede komponert, sykel. Returnerer et nytt parent-map.

**Hvordan går data inn og ut?**  
`layout_id` + `children` + kjente id-er + gjeldende parent-map inn; nytt parent-map ut, eller `CompositionError`. Dropp-ede barn får parent `None` (rot).

**Hvorfor er den bygget slik?**  
Sjekkene må testes uten display. Workspace eier Qt-reparenting.

**Naturlig videre utvikling**  
Ikke et komposisjonsrammeverk. Dybde er bare en intern sikkerhetsgrense mot uendelig vandring, ikke en layout-regel.
