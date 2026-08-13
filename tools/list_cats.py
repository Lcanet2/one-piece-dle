import sys, json, time; sys.path.insert(0,'.')
import wiki

def members(cat, limit=100000):
    out, cont = [], None
    while True:
        p = {"action":"query","list":"categorymembers","cmtitle":"Catégorie:"+cat,
             "cmlimit":500,"cmnamespace":0}
        if cont: p["cmcontinue"] = cont
        d = wiki.api(p)
        out += [m["title"] for m in d.get("query",{}).get("categorymembers",[])]
        cont = d.get("continue",{}).get("cmcontinue")
        if not cont or len(out) >= limit: break
        time.sleep(0.15)
    return out

cats = {
 "M": "Personnages Masculins", "F": "Personnages Féminins",
 "noncanon": "Personnages Non-Canon", "mentionnes": "Personnages Uniquement Mentionnés",
 "A": "Utilisateurs du Haki de l'armement", "O": "Utilisateurs du Haki de l'observation",
 "R": "Utilisateurs du Haki des rois",
}
res = {}
for k, c in cats.items():
    res[k] = members(c)
    print(f"  {c:<45} {len(res[k])}", flush=True)

json.dump(res, open('cats.json','w'), ensure_ascii=False)
hommes, femmes = set(res["M"]), set(res["F"])
tous = hommes | femmes
nc = set(res["noncanon"]) | set(res["mentionnes"])
canon = tous - nc
print(f"\n  total personnages genrés : {len(tous)}")
print(f"  dont non-canon / mentionnés : {len(tous & nc)}")
print(f"  → canon exploitable : {len(canon)}")
print(f"  déjà dans le jeu : ", end="")
import re
noms = [re.match(r'^\["([^"]+)"', l).group(1) for l in open('/home/leo/onepiecedle/js/characters.js',encoding='utf-8') if l.startswith('["')]
print(len(noms))
