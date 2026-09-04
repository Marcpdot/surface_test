# hermes_bridge.py

Source: `src/surface/hermes_bridge.py`

**Hva er ansvaret?**  
Er adapteren mellom rå ekstern tekst/JSON og Surface-protokollen.

**Hvordan går data inn og ut?**  
Rå streng fra bruker eller fremtidig Hermes-output går inn; en liste med validerte `Command`-objekter kommer ut.

**Hvorfor er den bygget slik?**  
Ekstern agentintegrasjon isoleres fra resten av Surface, slik at UI og core ikke trenger å vite hvordan Hermes kommuniserer.

**Naturlig videre utvikling**  
Når Hermes kobles på ekte kan transport, prompting og output-normalisering bygges her eller bak denne grensen uten å endre Surface-protokollen.