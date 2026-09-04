# blocks/image.py

Source: `src/surface/blocks/image.py`

**Hva er ansvaret?**  
Renderer en validert lokal bildefil som `ImageBlock` og håndterer skalering og fallback ved feil.

**Hvordan går data inn og ut?**  
En `ImageCommand` går inn; filen resolves via `image_source.py`, lastes som `QPixmap` og vises i widgeten.

**Hvorfor er den bygget slik?**  
Fil-policy og fil-I/O er skilt fra selve Qt-renderingen, slik at sikkerhets- og valideringsregler kan testes uten GUI.

**Naturlig videre utvikling**  
Naturlige neste steg er bedre sizing/cropping og senere interaksjon som zoom/pan når faktiske studiefigurer krever det.