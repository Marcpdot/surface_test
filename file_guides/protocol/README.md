# protocol.py

**Hva er ansvaret?**  
Definerer Surface sitt typesikre command-språk: hvilke command-typer som finnes, hvilke felt de har, og hvilke verdier som er gyldige.

**Hvordan går data inn og ut?**  
Rå JSON/dicts går inn i `parse_command` / `parse_command_list`; validerte `Command`-objekter kommer ut, eller en eksplisitt `ProtocolError`.

**Hvorfor er den bygget slik?**  
Systemgrensen trenger en liten, eksplisitt kontrakt som skiller rå input fra data resten av Surface kan stole på.

v0.2: `layout` er en command med `direction` (`vertical` | `horizontal`) og `children` (block-id-er). Nesting skjer ved at en layout refererer andre layout-id-er. Ukjente felter avvises.

v0.4: `move` og `remove` er eksplisitte workspace-operasjoner. `move.parent` bruker
layout-id eller `null` for root, og valgfri `index` angir nullbasert plassering.
Operasjonene er strengt feltvaliderte på samme måte som node-upserts.

v0.5: Ugyldig JSON forblir en streng `invalid_json`-feil fra `json.loads`.
Feilmeldingen tar med decoder-melding, linje, kolonne og tegnposisjon slik at
serialiseringsfeil kan diagnostiseres uten reparasjon eller permissiv parsing.

**Naturlig videre utvikling**
Utforsk type systems, grammars, algebraic data types, schemas og compositional interfaces før protocolen eventuelt generaliseres.
