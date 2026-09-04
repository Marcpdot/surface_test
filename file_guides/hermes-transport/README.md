# hermes_transport.py

Source: `src/surface/hermes_transport.py`

**Hva er ansvaret?**  
Utskiftbar I/O mot Hermes: `complete(prompt) -> str`. v0.3 har `CommandTransport` (ett subprocess per request) og `FakeTransport` for tester.

**Hvordan går data inn og ut?**  
Prompt blir siste argv-token (Hermes `hermes -z PROMPT`), stdin er DEVNULL. stdout/stderr dekodes som UTF-8. Feil blir `ProtocolError` (`hermes_unavailable`, `hermes_timeout`, `hermes_failed`). `SURFACE_HERMES_CMD` bør være `hermes -z` (bare `hermes` får `-z` innsatt slik at interaktiv CLI ikke startes). Optional `SURFACE_HERMES_TIMEOUT_S`.

**Hvorfor er den bygget slik?**  
Surface-core skal ikke vite hvordan Hermes startes. HTTP/keep-warm kan implementere samme protocol senere.

**Naturlig videre utvikling**  
Ikke modell-SDK i denne pakken.
