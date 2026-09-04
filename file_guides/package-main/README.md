# surface/__main__.py

Source: `src/surface/__main__.py`

**Hva er ansvaret?**  
Gjør at pakken kan startes med `python -m surface`.

**Hvordan går data inn og ut?**  
Python starter modulen; den delegerer direkte til `surface.app.main()`.

**Hvorfor er den bygget slik?**  
Entry point holdes ekstremt tynt, mens all faktisk oppstartslogikk ligger i `app.py`.

**Naturlig videre utvikling**  
Bør normalt ikke vokse; behold delegasjonen enkel.