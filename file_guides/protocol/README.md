# protocol.py

**Hva er ansvaret?**  
Definerer Surface sitt typesikre command-språk: hvilke command-typer som finnes, hvilke felt de har, og hvilke verdier som er gyldige.

**Hvordan går data inn og ut?**  
Rå JSON/dicts går inn i `parse_command` / `parse_command_list`; validerte `Command`-objekter kommer ut, eller en eksplisitt `ProtocolError`.

**Hvorfor er den bygget slik?**  
Systemgrensen trenger en liten, eksplisitt kontrakt som skiller rå input fra data resten av Surface kan stole på.

**Naturlig videre utvikling**  
Utforsk type systems, grammars, algebraic data types, schemas og compositional interfaces før protocolen eventuelt generaliseres.