# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
from urllib.parse import urlencode
from urllib.request import urlopen


# -----------------------------------------
# Database initialisatie en verbinden
# -----------------------------------------
# parameters voor connectie met de database
db = Database(host="localhost", gebruiker="root", wachtwoord="fekpon-qAvhem-kotbe9", database="attractiepark_casus_b")
# altijd verbinding openen om query"s uit te voeren
db.connect()


# -----------------------------------------
# Haal de eigenschappen op van een bezoeker
# -----------------------------------------
personeelslid_id = 4 # pas id aan om een ander personeelslid te selecteren

# SQL-query om alle gegevens van één personeelslid op te halen op basis van het ID.
select_query = f"SELECT * FROM personeelslid WHERE id = {personeelslid_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat
personeelslid = resultaat[0]

# voorbeeld van hoe je bij een eigenschap komt
print(personeelslid["naam"])

# -----------------------------------------
# Haal alle onderhoudstaken op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste onderhoudstaken op te halen
select_query = "SELECT * FROM onderhoudstaak WHERE afgerond = 0" # Alle onafgeronde onderhoudstaken
onderhoudstaken = db.execute_query(select_query)

# print de resultaten van de query op een overzichtelijke manier
#pprint.pp(onderhoudstaken) 

# print de omschrijving van de eerste onderhoudstaak
print(onderhoudstaken[0]["omschrijving"])

# Functie voor het bepalen van de maximale fysieke belasting
def maximale_fysieke_belasting():
    if personeelslid["verlaagde_fysieke_belasting"] == 0:
        if personeelslid["leeftijd"] <= 24:
            return 25
        elif personeelslid["leeftijd"] >= 25 and personeelslid["leeftijd"] <= 50:
            return 40
        elif personeelslid["leeftijd"] >= 51:
            return 15
    else:
        return personeelslid["verlaagde_fysieke_belasting"] # Advies arbo-arts is leidend
        
def pauze_opgesplitst():
    if personeelslid["pauze_opsplitsen"] == 1:
        return True
    else:
        return False

# Bevoegdheid van het personeelslid wordt opgedeeld in nummers. 1 = senior, 2 = medior, 3 = junior, 4 = stagiair
def bevoegdheid_bepalen_personeelslid():
    if personeelslid["bevoegdheid"] == "Senior":
        return 1;
    elif personeelslid["bevoegdheid"] == "Medior":
        return 2;
    elif personeelslid["bevoegdheid"] == "Junior":
        return 3;
    elif personeelslid["bevoegdheid"] == "Stagiair":
        return 4;

# Bevoegdheid van de taak wordt opgedeeld in nummers. 1 = senior, 2 = medior, 3 = junior, 4 = stagiair
def bevoegdheid_bepalen_taak(bevoegdheid):
        if bevoegdheid == "Senior":
            return 1;
        if bevoegdheid == "Medior":
            return 2;
        if bevoegdheid == "Junior":
            return 3;
        if bevoegdheid == "Stagiair":
            return 4;

def maak_dagtaak(taak):
    return { 
        "omschrijving" : taak["omschrijving"],
        "duur" : taak["duur"],
        "prioriteit" : taak["prioriteit"],
        "beroepstype" : taak["beroepstype"],
        "bevoegdheid" : taak["bevoegdheid"],
        "fysieke_belasting": taak["fysieke_belasting"],
        "attractie": taak["attractie"],
        "is_buitenwerk": taak["is_buitenwerk"]
    }

def haal_weergegevens_op(breedtegraad, lengtegraad): # Coordinaten op basis van database
    parameters = urlencode({
        "latitude": breedtegraad,
        "longitude": lengtegraad,
        "daily": "temperature_2m_max,precipitation_probability_mean",
        "timezone": "Europe/Amsterdam",
        "forecast_days": 1
    })

    url = "https://api.open-meteo.com/v1/forecast?" + parameters

    with urlopen(url, timeout=10) as antwoord:
        weerdata = json.load(antwoord)

    return {
        "temperatuur": weerdata["daily"]["temperature_2m_max"][0],
        "kans_op_regen": weerdata["daily"]["precipitation_probability_mean"][0]
    }

breedtegraad = 52.5125
lengtegraad = 6.09444
weergegevens = haal_weergegevens_op(breedtegraad, lengtegraad)


specialistische_attracties = personeelslid["specialist_in_attracties"].split(",") # Split bij elke komma
hoog_specialistisch = []
hoog_overig = []
laag_specialistisch = []
laag_overig = []

# Sorteren van de onderhoudstaken op of de taak specialistisch is en de prioriteit van de taak
for taak in onderhoudstaken:
    is_specialistisch = taak["attractie"] in specialistische_attracties

    if taak["prioriteit"] == "hoog":
        if is_specialistisch:
            hoog_specialistisch.append(taak)
        else:
            hoog_overig.append(taak)
    else:
        if is_specialistisch:
            laag_specialistisch.append(taak)
        else:
            laag_overig.append(taak)

gesorteerde_taken = hoog_specialistisch + hoog_overig + laag_specialistisch + laag_overig # List op volgorde van prioriteit, hoog naar laag

# Hier worden de taken uiteindelijk onder verdeeld op basis van meerdere criteria
def onderhoudstaken_verdelen():
    passende_taken = []
    resterende_werktijd = personeelslid["werktijd"]
    laatste_taak = ""

    # Bepalen van de laatste taak
    for taak in laag_overig + laag_specialistisch: # Eerst
        if (taak["duur"] <= 30
            and taak["duur"] <= personeelslid["werktijd"]
            and taak["beroepstype"] == personeelslid["beroepstype"]
            and bevoegdheid_bepalen_taak(taak["bevoegdheid"]) >= bevoegdheid_bepalen_personeelslid()
            and taak["fysieke_belasting"] <= maximale_fysieke_belasting()):
            laatste_taak = taak
            break # 

    resterende_werktijd -= laatste_taak["duur"]

    for taak in gesorteerde_taken: 
         # De laatste taak moet niet nog een x voorkomen
         if taak["id"] == laatste_taak["id"]:
             continue
         
         if (taak["beroepstype"] == personeelslid["beroepstype"] 
             and bevoegdheid_bepalen_taak(taak["bevoegdheid"]) >= bevoegdheid_bepalen_personeelslid()
             and taak["fysieke_belasting"] <= maximale_fysieke_belasting()):

            if taak['duur'] > resterende_werktijd:
                continue
            
            passende_taken.append(maak_dagtaak(taak))

            resterende_werktijd -= taak["duur"]
    passende_taken.append(maak_dagtaak(laatste_taak))
    totale_duur = personeelslid["werktijd"] - resterende_werktijd

    return passende_taken, totale_duur
              
passende_taken, totale_duur = onderhoudstaken_verdelen()

if personeelslid["werktijd"] > 330: # 5,5 uur 
    helft_werktijd = personeelslid["werktijd"] / 2
    gewerkte_minuten = 0

    # Standaard moet de pauze altijd voor de laatste taak komen
    pauze_plek = len(passende_taken) - 1

    for index in range(len(passende_taken) - 1): # Pauze mag niet op het einde komen
        gewerkte_minuten += passende_taken[index]["duur"]

        if gewerkte_minuten >= helft_werktijd:
            pauze_plek = index + 1
            break

    passende_taken.insert(pauze_plek, {"omschrijving": "Pauze", "duur": 30})
            
        
# print(onderhoudstaken_verdelen())        
# altijd verbinding sluiten met de database als je klaar bent
db.close()



# verzamel alle benodigde gegevens in een dictionary
dagtakenlijst = {
    "personeelsgegevens" : {
        "naam": personeelslid["naam"], # voorbeeld van hoe je bij een eigenschap komt
        "werktijd": personeelslid["werktijd"],
        "beroepstype": personeelslid["beroepstype"],
        "bevoegdheid": personeelslid["bevoegdheid"],
        "specialist in attracties": personeelslid["specialist_in_attracties"],
        "pauze opsplitsen": pauze_opgesplitst(),
        "leeftijd": personeelslid["leeftijd"],
        "maximale fysieke belasting": maximale_fysieke_belasting()
    },
    "weergegevens" : {
        "weergegevens": weergegevens
    }, 
    "dagtaken": passende_taken
        # TO-DO
        # Een dagtaak moet op meerdere punten gestorteerd worden
        # (AF) Het beroepstype past bij het beroep van het personeelslid 
        # (AF) De taak heeft een lagere fysieke belasting dan de maximale belasting van het personeelslid
        # (AF) Het personeel is bevoegd voor de taak
        # Er moet op basis van de beschikbare werktijd van het personeel bepaald worden hoeveel onderhoudstaken in het programma komen
        # Verschillende prioriteiteslevels
        # De laatste taak moet verplicht een lage prioriteit hebben en max 30 minuten duren
    

     # STAP 2: hier komt een lijst met alle dagtaken
    ,
    "totale_duur": totale_duur # STAP 3: aanpassen naar daadwerkelijke totale duur
}

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open("dagtakenlijst_personeelslid_x.json", "w") as json_bestand_uitvoer:
    json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)