# Code conventies

**Attractiepark Lake Side Mania**  
*BC1 - Software*

## Inleiding

Dit document bevat duidelijke en praktische codeconventies voor Python. Het is bedoeld als naslagbestand dat je naast je programmeerwerk kunt houden. Door deze richtlijnen consequent toe te passen, wordt je code beter leesbaar, begrijpelijker en eenvoudiger te onderhouden.

De richtlijnen zijn gebaseerd op algemeen geaccepteerde Python-afspraken (zoals PEP 8), maar vereenvoudigd.

## Structuur

Goede code-indeling zorgt ervoor dat de structuur van je Python-code direct zichtbaar is. Python gebruikt indentatie (inspringing) om blokken code aan te geven, bijvoorbeeld bij `if`-statements, functies en lussen.

### Richtlijnen voor structuur

- Plaats imports bovenaan het bestand.
- Splits je code op in functies in plaats van alles onder elkaar te schrijven.
- Houd functies kort en overzichtelijk: één functie doet bij voorkeur één ding.

## Naamgeving

Goede naamgeving maakt code begrijpelijk zonder extra uitleg. Namen moeten duidelijk beschrijven wat een variabele of functie doet.

### Richtlijnen voor naamgeving

- Gebruik één taal: Nederlands of Engels (niet door elkaar).
- Gebruik `snake_case` voor variabelen en functies.
- Gebruik zelfbeschrijvende namen (vermijd `x`, `data`, `tmp`).
- Gebruik meervoud voor lijsten, zodat direct duidelijk is dat het om meerdere waarden gaat.
- Gebruik `is_` of `has_`/`heeft_` voor booleans, zodat duidelijk is dat de waarde `True` of `False` is.

### Voorbeeld

```python
leeftijden = [18, 21, 30]

is_ingelogd = True
heeft_toegang = False

def bereken_gemiddelde(leeftijden):
    return sum(leeftijden) / len(leeftijden)
```

## Commentaar

Commentaar helpt om uit te leggen **waarom** code iets doet, niet **wat** het doet. Goede code is vaak al duidelijk door indeling en naamgeving.

### Richtlijnen voor commentaar

- Schrijf commentaar in één taal: Nederlands of Engels.
- Houd commentaar kort en duidelijk.
- Vermijd commentaar dat letterlijk herhaalt wat de code al zegt.
