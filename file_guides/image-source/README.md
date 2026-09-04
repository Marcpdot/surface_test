# image_source.py

Source: `src/surface/image_source.py`

**Hva er ansvaret?**  
Definerer policy og validering for hvilke lokale bildekilder Surface får lov til å lese.

**Hvordan går data inn og ut?**  
En path-streng går inn; en validert `Path` kommer ut, eller en eksplisitt `ProtocolError`.

**Hvorfor er den bygget slik?**  
Sikkerhets- og filregler holdes Qt-frie og kan derfor testes separat fra rendering.

**Naturlig videre utvikling**  
Utvid policyen bare når nye image-kilder faktisk trengs, for eksempel workspace-sandboxing eller eksplisitt asset-management.