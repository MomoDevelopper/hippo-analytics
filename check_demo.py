import sys
sys.path.insert(0, 'backend')
from scraper_lonab import generer_donnees_demo

d = generer_donnees_demo()
courses = d['courses']
print(f"Nb courses: {len(courses)}")
print(f"Clés d'une course: {list(courses[0].keys())}")

arrivee_val = courses[0].get("arrivee", "MANQUANT")
print(f"arrivee[0]: {arrivee_val}")
print(f"nb partants: {len(courses[0].get('partants', []))}")

sans_arrivee = [c for c in courses if not c.get('arrivee')]
print(f"Sans arrivee: {len(sans_arrivee)}/{len(courses)}")

avec_arrivee = [c for c in courses if c.get('arrivee')]
print(f"Avec arrivee: {len(avec_arrivee)}/{len(courses)}")
if avec_arrivee:
    ex = avec_arrivee[0]
    print(f"Exemple arrivee: {ex['arrivee']}")
    print(f"Partants: {len(ex['partants'])}")
