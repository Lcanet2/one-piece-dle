#!/usr/bin/env python3
"""Importe Images_One_Piece/ vers img/ en renommant chaque fichier d'après le slug
du personnage, puis régénère img/manifest.json.
Usage : python3 tools/import-images.py [dossier_source]"""
import json, os, re, shutil, sys, unicodedata, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'Images_One_Piece')
DEST = os.path.join(ROOT, 'img')
EXTS = {'.png', '.jpg', '.jpeg', '.webp'}

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', s)).strip()

def slug(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')

# ---- personnages ----
lines = [l for l in open(os.path.join(ROOT, 'js/characters.js'), encoding='utf-8') if l.startswith('["')]
names = [json.loads(l.rstrip().rstrip(','))[0] for l in lines]
by_norm = {norm(n): n for n in names}

# ---- alias du jeu, pour rattraper les noms de fichiers divergents ----
game = open(os.path.join(ROOT, 'js/game.js'), encoding='utf-8').read()
block = game[game.index('const ALIASES = {'):game.index('};', game.index('const ALIASES = {'))]
for k, v in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block):
    by_norm.setdefault(norm(k), v)
# titres du wiki
wl = open(os.path.join(ROOT, 'js/wikilinks.js'), encoding='utf-8')._read = None
src = open(os.path.join(ROOT, 'js/wikilinks.js'), encoding='utf-8').read()
for mine, title in json.loads(src[src.index('{'):src.rindex('}')+1]).items():
    by_norm.setdefault(norm(title), mine)

# ---- import ----
os.makedirs(DEST, exist_ok=True)
for f in os.listdir(DEST):
    if os.path.splitext(f)[1].lower() in EXTS:
        os.remove(os.path.join(DEST, f))

matched, unmatched = {}, []
for f in sorted(os.listdir(SRC)):
    base, ext = os.path.splitext(f)
    if ext.lower() not in EXTS:      # ignore les Zone.Identifier et autres
        continue
    perso = by_norm.get(norm(base))
    if not perso:
        unmatched.append(f); continue
    if perso in matched:             # doublon : on garde le premier
        unmatched.append(f + "  (doublon de " + perso + ")"); continue
    dest = slug(perso) + ext.lower()
    shutil.copy2(os.path.join(SRC, f), os.path.join(DEST, dest))
    matched[perso] = dest

manifest = {os.path.splitext(v)[0]: v for v in sorted(matched.values())}
json.dump(manifest, open(os.path.join(DEST, 'manifest.json'), 'w'),
          ensure_ascii=False, indent=1, sort_keys=True)

sans = [n for n in names if n not in matched]
print(f"Images importées : {len(matched)} / {len(names)} personnages")
print(f"Poids total      : {sum(os.path.getsize(os.path.join(DEST,v)) for v in matched.values())/1048576:.1f} Mo")
if sans:
    print(f"\nSans image ({len(sans)}) :")
    for n in sans: print("   -", n)
if unmatched:
    print(f"\nFichiers non rattachés ({len(unmatched)}) :")
    for f in unmatched: print("   -", f)
