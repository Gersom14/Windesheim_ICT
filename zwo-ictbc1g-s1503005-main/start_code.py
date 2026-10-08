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
personeelslid_id = input("Voor welk personeelslid wil je een dagtakenlijst aanmaken? ") # Pas id aan om een ander personeelslid te selecteren

# SQL-query om alle gegevens van één personeelslid op te halen op basis van het ID.
select_query = f"SELECT * FROM personeelslid WHERE id = {personeelslid_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat
personeelslid = resultaat[0]

# -----------------------------------------
# Haal alle onderhoudstaken op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste onderhoudstaken op te halen
select_query = "SELECT * FROM onderhoudstaak WHERE afgerond = 0" # Alle afgeronde onderhoudstaken worden eruit gefilterd
onderhoudstaken = db.execute_query(select_query)

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

# Bepalen of de pauze opgesplitst moet worden
# 1 of 0 omzetten naar True of False
def pauze_opgesplitst():
    if personeelslid["pauze_opsplitsen"] == 1:
        return True
    else:
        return False

# Bevoegdheid van het personeelslid en de taak wordt opgedeeld in nummers. 1 = senior, 2 = medior, 3 = junior, 4 = stagiair
bevoegdheidniveaus = {
    "Senior": 1,
    "Medior": 2,
    "Junior": 3,
    "Stagiair": 4
}

def is_bevoegd(personeelslid, taak):
    bevoegdheid_persoon = bevoegdheidniveaus[personeelslid["bevoegdheid"]]
    bevoegdheid_taak = bevoegdheidniveaus[taak["bevoegdheid"]]

    return bevoegdheid_persoon <= bevoegdheid_taak

# De dagtaak in JSON formaat zetten
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

def maak_personeelsgegevens(personeelslid):
    return {
        "naam": personeelslid["naam"],
        "werktijd": personeelslid["werktijd"],
        "beroepstype": personeelslid["beroepstype"],
        "bevoegdheid": personeelslid["bevoegdheid"],
        "specialist_in_attracties": personeelslid["specialist_in_attracties"],
        "pauze_opsplitsen": pauze_opgesplitst(),
        "max_fysieke_belasting": maximale_fysieke_belasting()
    }

# Het ophalen van de weergegevens door middel van de Meteo API
def haal_weergegevens_op(breedtegraad, lengtegraad): 
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

# Lake Side Mania is gevestigd in Zwolle
breedtegraad = 52.5125
lengtegraad = 6.09444
weergegevens = haal_weergegevens_op(breedtegraad, lengtegraad)

# Lijsten voor de verschillende soorten attracties
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
    for taak in laag_overig: 
        if (taak["duur"] <= 30
            and taak["duur"] <= personeelslid["werktijd"]
            and taak["beroepstype"] == personeelslid["beroepstype"]
            and is_bevoegd(personeelslid, taak)
            and taak["fysieke_belasting"] <= maximale_fysieke_belasting()):
            laatste_taak = taak
            break 

    resterende_werktijd -= laatste_taak["duur"]

    for taak in gesorteerde_taken: 
         # De laatste taak moet niet nog een x voorkomen
         if taak["id"] == laatste_taak["id"]:
             continue

         #Dagtaken filteren op meerdere eisen
         if (taak["beroepstype"] == personeelslid["beroepstype"] 
             and is_bevoegd(personeelslid, taak)
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

        if gewerkte_minuten >= helft_werktijd: # Na deze plek wordt de pauze ingevoegd
            pauze_plek = index + 1
            break

    passende_taken.insert(pauze_plek, {"omschrijving": "Pauze", "duur": 30})
            
        
# altijd verbinding sluiten met de database als je klaar bent
db.close()

# Vraag de personeelsgegevens op
personeelgegevens = maak_personeelsgegevens(personeelslid)

# verzamel alle benodigde gegevens in een dictionary
dagtakenlijst = {
    "personeelsgegevens" : personeelgegevens,
    "weergegevens" : weergegevens, 
    "dagtaken": passende_taken
    ,
    "totale_duur": totale_duur # STAP 3: aanpassen naar daadwerkelijke totale duur
}

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open("dagtakenlijst_personeelslid_x.json", "w") as json_bestand_uitvoer:
    json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)