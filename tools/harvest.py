import sys, json, re, os, time; sys.path.insert(0,'.')
import wiki

CACHE = 'allchars.json'
cats  = json.load(open('cats.json'))
tous  = set(cats["M"]) | set(cats["F"])
canon = sorted(tous - set(cats["noncanon"]) - set(cats["mentionnes"]))
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def batch(titles, size=25):
    for i in range(0, len(titles), size):
        yield titles[i:i+size]

def fetch(titles):
    out = {}
    d = wiki.api({"action":"query","titles":"|".join(titles),
                  "prop":"revisions","rvprop":"content","rvslots":"main","redirects":1})
    q = d.get("query", {})
    back = {}
    for n in q.get("normalized",[]): back[n["to"]] = n["from"]
    for r in q.get("redirects",[]):  back[r["to"]] = r["from"]
    for p in q.get("pages",{}).values():
        t = p.get("title",""); src = back.get(t,t)
        while src in back: src = back[src]
        if "revisions" in p:
            out[src] = p["revisions"][0]["slots"]["main"]["*"]
    return out

# ---- passe 1 : articles ----
todo = [t for t in canon if t not in cache]
print(f"{len(canon)} personnages canon, {len(todo)} à récupérer", flush=True)
besoin_tpl = {}
for i, ch in enumerate(batch(todo)):
    try: pages = fetch(ch)
    except Exception as e:
        print("  erreur lot", i, e, flush=True); time.sleep(3); continue
    for t, wt in pages.items():
        if "{{Char box" in wt:
            cache[t] = wt
        else:
            m = re.match(r'\s*\{\{([^|}\n]{2,40})[|}]', wt)
            if m and m.group(1).strip().lower() not in ('spoil','citation','pagesbloquées','homonymie'):
                besoin_tpl[t] = m.group(1).strip()
            else:
                m2 = re.findall(r'\{\{([^|}\n]{2,40})[|}]', wt[:300])
                cand = [x.strip() for x in m2 if x.strip().lower() not in ('spoil','citation','pagesbloquées','homonymie')]
                if cand: besoin_tpl[t] = cand[0]
    if i % 10 == 0:
        json.dump(cache, open(CACHE,'w'), ensure_ascii=False)
        print(f"  lot {i} — {len(cache)} fiches, {len(besoin_tpl)} via template", flush=True)
    time.sleep(0.2)

json.dump(cache, open(CACHE,'w'), ensure_ascii=False)
json.dump(besoin_tpl, open('need_tpl.json','w'), ensure_ascii=False)
print(f"passe 1 terminée : {len(cache)} fiches directes, {len(besoin_tpl)} à chercher en template", flush=True)

# ---- passe 2 : templates ----
inv = {}
for art, tpl in besoin_tpl.items():
    inv.setdefault("Modèle:"+tpl, art)
noms = [t for t in inv if inv[t] not in cache]
for i, ch in enumerate(batch(noms)):
    try: pages = fetch(ch)
    except Exception as e:
        print("  erreur tpl", i, e, flush=True); time.sleep(3); continue
    for t, wt in pages.items():
        if "{{Char box" in wt and t in inv:
            cache[inv[t]] = wt
    if i % 10 == 0:
        json.dump(cache, open(CACHE,'w'), ensure_ascii=False)
        print(f"  tpl lot {i} — {len(cache)} fiches", flush=True)
    time.sleep(0.2)

json.dump(cache, open(CACHE,'w'), ensure_ascii=False)
print(f"\nTERMINÉ : {len(cache)} / {len(canon)} fiches avec infobox", flush=True)
print("sans infobox :", len([t for t in canon if t not in cache]), flush=True)
