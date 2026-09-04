# blocks/equation.py

Source: `src/surface/blocks/equation.py`

**Hva er ansvaret?**  
Renderer `EquationCommand` som et matematisk uttrykk ved å bruke matplotlib mathtext og vise resultatet som `QPixmap`.

**Hvordan går data inn og ut?**  
LaTeX-streng + display-modus går inn; et rasterisert matematikkuttrykk eller kontrollert fallback vises i widgeten.

**Hvorfor er den bygget slik?**  
Den gir matematisk rendering uten en full system-LaTeX-installasjon og holder ligningslogikken separat fra resten av UI-et.

**Naturlig videre utvikling**  
Bytt renderer først når reelle uttrykk krever mer enn mathtext; behold command-kontrakten stabil hvis mulig.