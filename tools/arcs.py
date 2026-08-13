# Bornes de chapitres des arcs. Le dernier arc est ouvert.
ARCS = [
    (1,    "Romance Dawn"),
    (8,    "Ville d'Orange"),
    (22,   "Village de Syrup"),
    (42,   "Baratie"),
    (69,   "Arlong Park"),
    (96,   "Loguetown"),
    (101,  "Reverse Mountain"),
    (106,  "Whisky Peak"),
    (115,  "Little Garden"),
    (130,  "Drum"),
    (155,  "Alabasta"),
    (218,  "Jaya"),
    (237,  "Skypiea"),
    (303,  "Long Ring Long Land"),
    (322,  "Water 7"),
    (375,  "Enies Lobby"),
    (431,  "Post-Enies Lobby"),
    (442,  "Thriller Bark"),
    (490,  "Sabaody"),
    (514,  "Amazon Lily"),
    (525,  "Impel Down"),
    (550,  "Marineford"),
    (581,  "Après-guerre"),
    (598,  "Retour à Sabaody"),
    (603,  "Ile des Hommes-Poissons"),
    (654,  "Punk Hazard"),
    (700,  "Dressrosa"),
    (802,  "Zou"),
    (825,  "Whole Cake Island"),
    (903,  "Reverie"),
    (909,  "Wano"),
    (1058, "Egghead"),
    (1126, "Elbaf"),
]
NOMS = [n for _, n in ARCS]
def arc(ch):
    nom = ARCS[0][1]
    for debut, n in ARCS:
        if ch >= debut: nom = n
        else: break
    return nom
