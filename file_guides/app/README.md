# app.py

Source: `src/surface/app.py`

**Hva er ansvaret?**  
Bootstrapper applikasjonen: CLI-argumenter, Qt/matplotlib-oppsett, `QApplication`, hovedvindu og event loop.

**Hvordan går data inn og ut?**  
CLI-argumenter går inn; appen starter normal, demo eller inject-modus og returnerer en prosess-exitkode.

**Hvorfor er den bygget slik?**  
Oppstart og runtime-konfigurasjon holdes samlet og separert fra selve UI- og domain-logikken.

**Naturlig videre utvikling**  
Legg bare til nye startup-modes/config når de er reelle systembehov; hold application bootstrap liten.