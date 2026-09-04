# blocks/base.py

Source: `src/surface/blocks/base.py`

**Hva er ansvaret?**  
Definerer minimumskontrakten alle renderbare Surface-blocks må følge.

**Hvordan går data inn og ut?**  
En block har en stabil `command_id`, rapporterer sin `command_type`, og mottar en `Command` i `render()`.

**Hvorfor er den bygget slik?**  
Felles kontrakt gjør at workspace kan behandle ulike representasjoner likt uten å kjenne implementasjonen deres.

**Naturlig videre utvikling**  
Bare legg til felles capabilities når flere block-typer faktisk deler dem; unngå å gjøre basisklassen til en stor generell UI-abstraksjon.