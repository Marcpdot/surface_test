# surface/__init__.py

Source: `src/surface/__init__.py`

**Hva er ansvaret?**  
Markerer `surface` som Python-pakke og eksponerer versjonsnummeret.

**Hvordan går data inn og ut?**  
Ingen runtime-dataflyt; import av pakken gjør `__version__` tilgjengelig.

**Hvorfor er den bygget slik?**  
Pakkeidentitet og enkel offentlig metadata holdes minimal.

**Naturlig videre utvikling**  
Eksponer bare bevisst valgte offentlige symboler her; unngå å gjøre fila til en stor import-hub.