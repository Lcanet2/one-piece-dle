import json, re, sys, time, urllib.parse, urllib.request

API = "https://onepiece.fandom.com/fr/api.php"
UA  = {"User-Agent": "onepiecedle-data-check/1.0 (personal fan project)"}

def api(params):
    params = dict(params); params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            if attempt == 2: raise
            time.sleep(1.5)

def fetch_templates(titles):
    """titles -> {title: wikitext} pour Modèle:<title>, par lots de 50"""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i+50]
        d = api({"action":"query","titles":"|".join("Modèle:"+t for t in chunk),
                 "prop":"revisions","rvprop":"content","rvslots":"main"})
        q = d.get("query", {})
        norm = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for p in q.get("pages", {}).values():
            t = p.get("title","")
            t = norm.get(t, t)
            t = t.replace("Modèle:", "", 1)
            if "revisions" in p:
                out[t] = p["revisions"][0]["slots"]["main"]["*"]
        time.sleep(0.3)
    return out

def search(name):
    d = api({"action":"query","list":"search","srsearch":name,"srlimit":3,"srnamespace":0})
    return [r["title"] for r in d.get("query",{}).get("search",[])]

FIELD_RE = re.compile(r'^\|\s*([^=|{}\[\]\n]+?)\s*=\s*(.*)$')

def parse_fields(wt):
    """Découpe le wikitext de l'infobox en {champ: valeur brute multi-ligne}"""
    fields, cur = {}, None
    for line in wt.split("\n"):
        m = FIELD_RE.match(line)
        if m:
            cur = m.group(1).strip().lower()
            fields.setdefault(cur, "")
            fields[cur] += m.group(2)
        elif cur is not None:
            if line.startswith("}}") or line.startswith("{{Char box") or line.startswith("{{Onglets"):
                cur = None
            else:
                fields[cur] += "\n" + line
    return fields

def strip_wiki(s):
    s = re.sub(r'\{\{Qref[^{}]*(\{\{[^{}]*\}\}[^{}]*)*\}\}', '', s, flags=re.I)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', s)
    s = re.sub(r"'''?", '', s)
    return s

def _montants(txt):
    """Montants en berries trouvés dans un fragment d'infobox."""
    def _n(t):
        v = re.sub(r'[.,\s ]', '', t)
        return int(v) if v.isdigit() else None
    nums = [n for n in (_n(m) for m in re.findall(r'\{\{B[^}]*\}\}\s*([\d.,\s ]+)', txt)) if n]
    if not nums:
        nums = [n for n in (_n(m) for m in re.findall(r'\d[\d.,\s ]{5,}', txt)) if n]
    return [n for n in nums if 1 <= n <= 10**13]

def get_bounty(fields):
    raw = fields.get("prime", "")
    # notation "étoiles/couronnes" des Marines : traitée ailleurs
    if "★" in raw or "{{C|" in raw or "{{c|" in raw:
        return None
    raw = strip_wiki(raw)
    if not raw.strip(): return None

    # Les primes barrées sont celles qui ne sont plus actives : mort, capture,
    # grâce, ou simple révision à la hausse. On les écarte tant qu'il reste une
    # prime active ; sinon on garde la dernière connue — sans quoi Arlong,
    # Doflamingo ou Roger apparaîtraient sans prime du tout.
    barrees = re.findall(r'<s>(.*?)</s>|<strike>(.*?)</strike>', raw, flags=re.S|re.I)
    barrees = " ".join(a or b for a, b in barrees)
    actif = re.sub(r'<s>.*?</s>|<strike>.*?</strike>', ' ', raw, flags=re.S|re.I)
    actif = re.sub(r'[^\n]*\(?anciennement\)?[^\n]*', ' ', actif, flags=re.I)

    nums = _montants(actif) or _montants(barrees) or _montants(raw)
    return max(nums) if nums else None

def get_height(fields):
    raw = strip_wiki(fields.get("taille", ""))
    vals = []
    # format "1m74" / "12m50"
    for m in re.finditer(r'(\d+)\s*m\s*(\d{2})(?!\d)', raw, re.I):
        vals.append(int(m.group(1)) * 100 + int(m.group(2)))
    raw2 = re.sub(r'\d+\s*m\s*\d{2}(?!\d)', ' ', raw, flags=re.I)
    for m in re.finditer(r'(\d+(?:[.,]\d+)?)\s*(cm|m\b|mètres?)', raw2, re.I):
        v = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        cm = v if unit == "cm" else v * 100
        if 20 <= cm <= 200000: vals.append(cm)
    return int(round(max(vals))) if vals else None

def get_fruit_type(fields):
    raw = strip_wiki(fields.get("dftype", "") + " " + fields.get("dfnom", ""))
    low = raw.lower()
    if "mythique" in low: return "Zoan Mythique"
    if "ancestral" in low or "préhistorique" in low: return "Zoan Ancestral"
    if "zoan" in low: return "Zoan"
    if "logia" in low: return "Logia"
    if "paramecia" in low: return "Paramecia"
    return None

def get_origin(fields):
    raw = strip_wiki(fields.get("origine", ""))
    for k in ["East Blue","West Blue","North Blue","South Blue","Île des Hommes-Poissons",
              "Île Des Hommes-Poissons","Wano","Elbaf","Grand Line","Nouveau Monde",
              "Mary Joa","Ciel","Skypiea","Île Céleste"]:
        if k.lower() in raw.lower(): return k
    return raw.strip().split("\n")[0][:40] or None

def get_status(fields):
    return strip_wiki(fields.get("statut","")).strip().split("\n")[0][:30] or None
