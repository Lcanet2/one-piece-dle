#!/usr/bin/env python3
"""Régénère PERSONNAGES.txt à partir de js/characters.js.
Usage : python3 tools/build-list.py"""
import json, collections, unicodedata, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lines = [l for l in open(os.path.join(ROOT, 'js/characters.js'), encoding='utf-8') if l.startswith('["')]
rows  = [json.loads(l.rstrip().rstrip(',')) for l in lines]
F = ["nom","genre","equipage","camp","fruit","haki","prime","taille","origine","saga"]
chars = [dict(zip(F, r)) for r in rows]

# les indices emoji sont dans js/emoji.js
import json as _j
_src = open(os.path.join(ROOT, 'js/emoji.js'), encoding='utf-8').read()
_emo = _j.loads(_src[_src.index('{'):_src.rindex('}')+1])
for c in chars:
    c["emoji"] = _emo.get(c["nom"], "")

def fmt_prime(v):
    if v < 0:  return "?"
    if v == 0: return "aucune"
    return f"{v:,}".replace(",", " ") + " B"

def fmt_taille(v):
    if v < 0: return "?"
    return f"{v/100:.2f} m".replace(".", ",") if v >= 100 else f"{v} cm"

def fmt_haki(h):
    n = {"A":"Armement", "O":"Observation", "R":"Rois"}
    return " + ".join(n[x] for x in h) if h else "—"

GENRE = {"M":"Homme", "F":"Femme", "?":"Inconnu"}
def sortkey(s):
    return unicodedata.normalize('NFD', s).encode('ascii','ignore').decode().lower()

groups = collections.defaultdict(list)
for c in chars:
    groups[c["equipage"]].append(c)

W = 100
out = []
out.append("=" * W)
out.append("ONE PIECE DLE — LISTE DES PERSONNAGES".center(W))
out.append(f"{len(chars)} personnages · {len(groups)} affiliations".center(W))
out.append("=" * W)
out.append("")
out.append("Recensement complet des personnages canon de One Piece Encyclopédie (onepiece.fandom.com/fr).")
out.append("Prime : « ? » = non révélée dans l'œuvre · « aucune » = pas de prime (Marines, civils…).")
out.append("Taille : « ? » = non révélée.  Haki : « — » = aucun connu.")
out.append("")

out.append("#" * W)
out.append("  1. PAR AFFILIATION")
out.append("#" * W)
for equipage in sorted(groups, key=sortkey):
    membres = sorted(groups[equipage], key=lambda c: sortkey(c["nom"]))
    out.append("")
    entete = f"── {equipage.upper()}  ({len(membres)}) "
    out.append(entete + "─" * max(0, W - len(entete)))
    for c in membres:
        out.append(f"  {c['nom']:<32} {c['emoji']}")
        out.append(f"     {GENRE[c['genre']]:<8} · {c['fruit']:<15} · Haki : {fmt_haki(c['haki'])}")
        out.append(f"     Prime : {fmt_prime(c['prime']):<18} Taille : {fmt_taille(c['taille']):<10} "
                   f"Origine : {c['origine']:<26} 1re app. : {c['saga']}")

out.append("")
out.append("#" * W)
out.append("  2. INDEX ALPHABÉTIQUE")
out.append("#" * W)
out.append("")
for c in sorted(chars, key=lambda c: sortkey(c["nom"])):
    out.append(f"  {c['nom']:<34} {c['equipage']:<38} {fmt_prime(c['prime']):>18}")

avec = [c for c in chars if c["prime"] > 0]
out.append("")
out.append("#" * W)
out.append(f"  3. CLASSEMENT DES PRIMES  ({len(avec)} personnages à prime connue)")
out.append("#" * W)
out.append("")
for i, c in enumerate(sorted(avec, key=lambda c: -c["prime"]), 1):
    out.append(f"  {i:>3}. {c['nom']:<34} {fmt_prime(c['prime']):>18}   {c['equipage']}")

out.append("")
out.append("#" * W)
out.append("  4. RÉPARTITIONS")
out.append("#" * W)
for champ, label in [("camp","Camp"), ("fruit","Fruit du Démon"),
                     ("origine","Origine"), ("saga","Première apparition")]:
    out.append("")
    out.append(f"  {label} :")
    for val, n in collections.Counter(c[champ] for c in chars).most_common():
        out.append(f"     {val:<32} {n:>4}  {'█' * round(n / 2)}")

dest = os.path.join(ROOT, 'PERSONNAGES.txt')
open(dest, 'w', encoding='utf-8').write("\n".join(out) + "\n")
print(f"PERSONNAGES.txt régénéré — {len(chars)} personnages, {len(out)} lignes")
