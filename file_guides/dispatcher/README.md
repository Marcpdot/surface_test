# dispatcher.py

Source: `src/surface/dispatcher.py`

**Hva er ansvaret?**  
Ruter en allerede validert `Command` til workspace og gjør resultatet eksplisitt som `DispatchResult`.

**Hvordan går data inn og ut?**  
En typed `Command` går inn; resultatet av create/update eller en kontrollert dispatch-feil kommer ut.

**Hvorfor er den bygget slik?**  
Den skiller command-språket fra UI/rendering og holder selve rutingen Qt-fri og testbar.

v0.4: `dispatch_many` er en atomisk batch. Suksess gir én result per command;
valideringsfeil gir én feilresultat for kommandoen som avbrøt batchen, uten mutasjon.
Actions er `created`, `updated`, `moved` eller `removed`.

**Naturlig videre utvikling**
Utvid bare hvis routing trenger flere handlinger, transaksjoner eller rikere resultater; ellers bør denne forbli liten.
