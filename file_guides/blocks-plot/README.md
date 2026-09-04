# blocks/plot.py

Source: `src/surface/blocks/plot.py`

**Hva er ansvaret?**  
Renderer strukturerte plot-data som line-, scatter- eller bar-plots med matplotlib i Qt.

**Hvordan går data inn og ut?**  
En `PlotCommand` med validerte serier går inn; en matplotlib-figur bygges og vises via `FigureCanvasQTAgg`.

**Hvorfor er den bygget slik?**  
AI/protocol sender data, ikke kjørbar plotting-kode; rendereren eier visualiseringen og holder execution-grensen trygg.

**Naturlig videre utvikling**  
Legg til nye plot-capabilities gjennom eksplisitte schemafelt når reelle behov oppstår, og vurder interaktiv plotting først når det gir studie- eller engineering-verdi.