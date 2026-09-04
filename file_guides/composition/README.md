# composition.py

Source: `src/surface/composition.py`

**Hva er ansvaret?**  
Qt-fri semantisk workspace-state og atomisk batch-planlegging. Validerer identitet,
ownership, root-/child-rekkefølge, flytting, fjerning, kapasitet og sykler før Qt røres.

**Hvordan går data inn og ut?**  
`WorkspaceState` + en ferdig parset command-liste inn; `BatchPlan` med ny state og
actions ut, eller `CompositionError`. Den opprinnelige staten muteres aldri.

**Hvorfor er den bygget slik?**  
Sjekkene må testes uten display. Workspace eier Qt-reparenting.

**Naturlig videre utvikling**  
Dette er fortsatt ikke en generell layoutmotor: modellen kjenner bare root, vertikale/
horisontale layouts og de eksplisitte `move`/`remove`-operasjonene.
