# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database


# -----------------------------------------
# Database initialisatie en verbinden
# -----------------------------------------
# parameters voor connectie met de database
db = Database(host="localhost", gebruiker="root", wachtwoord="fekpon-qAvhem-kotbe9", database="attractiepark_casus_b")
# altijd verbinding openen om query's uit te voeren
db.connect()


# -----------------------------------------
# Haal de eigenschappen op van een bezoeker
# -----------------------------------------
personeelslid_id = 2 # pas id aan om een ander personeelslid te selecteren

# SQL-query om alle gegevens van één personeelslid op te halen op basis van het ID.
select_query = f"SELECT * FROM personeelslid WHERE id = {personeelslid_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat
personeelslid = resultaat[0]

# voorbeeld van hoe je bij een eigenschap komt
print(personeelslid['naam'])

# -----------------------------------------
# Haal alle onderhoudstaken op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste onderhoudstaken op te halen
select_query = "SELECT * FROM onderhoudstaak"
onderhoudstaken = db.execute_query(select_query)

# print de resultaten van de query op een overzichtelijke manier
##pprint.pp(onderhoudstaken) 

# print de omschrijving van de eerste onderhoudstaak
print(onderhoudstaken[0]["omschrijving"])

# functie voor het bepalen van de maximale fysieke belasting
def maximale_fysieke_belasting():
    if personeelslid['verlaagde_fysieke_belasting'] == 0:
        if personeelslid['leeftijd'] <= 24:
            return 25
        elif personeelslid['leeftijd'] >= 25 and personeelslid['leeftijd'] <= 50:
            return 40
        elif personeelslid['leeftijd'] >= 51:
            return 15
    else:
        return personeelslid['verlaagde_fysieke_belasting']
        
def pauze_opgesplitst():
    if personeelslid['pauze_opsplitsen'] == 1:
        return True
    else:
        return False

# altijd verbinding sluiten met de database als je klaar bent
db.close()



# verzamel alle benodigde gegevens in een dictionary
dagtakenlijst = {
    "personeelsgegevens" : {
        "naam": personeelslid['naam'], # voorbeeld van hoe je bij een eigenschap komt
        "werktijd": personeelslid['werktijd'],
        "beroepstype": personeelslid['beroepstype'],
        "bevoegdheid": personeelslid['bevoegdheid'],
        "specialist in attracties": personeelslid['specialist_in_attracties'],
        "pauze opsplitsen": pauze_opgesplitst(),
        "leeftijd": personeelslid['leeftijd'],
        "maximale fysieke belasting": maximale_fysieke_belasting()

        #"verlaagde fysieke belasting": personeelslid['verlaagde_fysieke_belasting']
    },
    "weergegevens" : {
        # STAP 4: vul aan met weergegevens (DP9)
    }, 
    "dagtaken": [] # STAP 2: hier komt een lijst met alle dagtaken
    ,
    "totale_duur": 0 # STAP 3: aanpassen naar daadwerkelijke totale duur
}

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagtakenlijst_personeelslid_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)