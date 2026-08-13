import sys, json, re, collections; sys.path.insert(0,'.')
import wiki
ROOT='/home/leo/onepiecedle/'

cures   = json.load(open('wikicache.json'))     # {nom curé: {title, wt}}
tous    = json.load(open('allchars.json'))      # {titre wiki: wt}
cats    = json.load(open('cats.json'))
src     = open(ROOT+'js/wikilinks.js',encoding='utf-8').read()
links   = json.loads(src[src.index('{'):src.rindex('}')+1])

GENRE={}
for t in cats["M"]: GENRE[t]="M"
for t in cats["F"]: GENRE[t]="F"
HAKI=collections.defaultdict(str)
for k in "AOR":
    for t in cats[k]: HAKI[t]+=k

# Arc de première apparition, déduit du numéro de chapitre (tools/arcs.py).
# Granularité arc et non saga : Sabaody appartient à la saga de la Guerre au
# Sommet, mais afficher « Sabaody » est bien plus parlant.
sys.path.insert(0, ROOT+'tools')
from arcs import arc, NOMS as ARCS

CAMPS=[
 # ordre important : le plus spécifique d'abord
 ("cipher pol","Gouvernement"),("cp-","Gouvernement"),("cp0","Gouvernement"),("aigis","Gouvernement"),
 ("révolutionnaire","Revolutionnaire"),("armée de la liberté","Revolutionnaire"),
 ("marine","Marine"),
 ("gouvernement mondial","Gouvernement"),("impel down","Gouvernement"),("dragon céleste","Gouvernement"),
 ("tribunal","Gouvernement"),("g-","Marine"),
 ("kozuki","Samourai"),("fourreaux rouges","Samourai"),("pays des wa","Samourai"),("pays de wa","Samourai"),("samouraï","Samourai"),
 ("équipage","Pirate"),("pirate","Pirate"),("famille charlotte","Pirate"),("barbe blanche","Pirate"),
 ("barbe noire","Pirate"),("thriller bark","Pirate"),("kuja","Pirate"),("baroque works","Pirate"),
 ("cent bêtes","Pirate"),("don quijote","Pirate"),("big mom","Pirate"),("spade","Pirate"),
 ("géant","Geant"),
]
def camp(t):
    t=t.lower()
    for k,v in CAMPS:
        if k in t: return v
    return "Civil"
ORIG=[("pays des wa","Wano"),("erbaf","Elbaf"),("elbaf","Elbaf"),("hommes-poissons","Ile des Hommes-Poissons"),
      ("ryugu","Ile des Hommes-Poissons"),("célestes","Ciel"),("skypiea","Ciel"),("amazon lily","Calm Belt"),
      ("calm belt","Calm Belt"),("mary joa","Terre Sainte de Mary Joa"),("marie-joie","Terre Sainte de Mary Joa"),
      ("logue town","East Blue"),("east blue","East Blue"),("west blue","West Blue"),("north blue","North Blue"),
      ("south blue","South Blue"),("grand line","Grand Line"),("zou","Grand Line"),("nouveau monde","Grand Line")]
def origine(f):
    t=wiki.strip_wiki(f.get("origine","")).lower()
    for k,v in ORIG:
        if k in t: return v
    return "Inconnue"
def fruit(f):
    r=(wiki.strip_wiki(f.get("dftype",""))+" "+wiki.strip_wiki(f.get("dfnom",""))).lower()
    if not r.strip(): return "Aucun"
    for k,v in [("mythique","Zoan Mythique"),("antique","Zoan Ancestral"),("ancestral","Zoan Ancestral"),
                ("préhistorique","Zoan Ancestral"),("zoan","Zoan"),("logia","Logia"),("paramecia","Paramecia")]:
        if k in r: return v
    return "Aucun"
def prime(f):
    raw=f.get("prime","")
    if "★" in raw or "{{C|" in raw or "{{c|" in raw:   # 1 étoile = 100 M, 1 couronne = 1 Md
        v=raw.count("★")*100_000_000+sum(int(x) for x in re.findall(r'\{\{[Cc]\|(\d+)\}\}',raw))*1_000_000_000
        return v or None
    return wiki.get_bounty(f)
# Membres d'origine de l'équipage : affiliation unifiée
CORE = {"Monkey D. Luffy","Roronoa Zoro","Nami","Usopp","Sanji","Tony Tony Chopper",
        "Nico Robin","Franky","Brook","Jinbe"}
CREW = "Équipage du Chapeau de Paille"

# À ignorer quand on cherche l'équipage d'origine d'un allié :
# la flotte de Luffy, le colisée de Dressrosa, les espèces et les lieux génériques.
def _ignorer(x):
    t = x.lower()
    if "chapeau de paille" in t and "faux" not in t: return True   # flotte / alliance
    if "armada de chapeau" in t: return True
    if re.match(r'(chapitre|épisode|tome|sbs)\s*\d', t): return True   # référence ayant débordé
    return t.strip() in ("colisée corrida","nain","nains","géant","géants","humain","humains")

def liens(v):
    return [m.group(1).strip() for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', v)]

ANCIEN = re.compile(r'anciennement|ancien\b|ex-', re.I)

def lien1(v):
    """Affiliation principale : on privilégie les lignes qui ne sont pas
    marquées « (anciennement) », sinon Koby resterait rattaché à l'équipage
    d'Alvida au lieu de la Marine."""
    segments = [seg for seg in re.split(r'<br\s*/?>|\n', v) if seg.strip()]
    actuels  = [seg for seg in segments if not ANCIEN.search(seg)]
    for source in (actuels, segments):
        for seg in source:
            for x in liens(seg):
                if not _ignorer(x): return x[:42]
    ls = liens(v)
    if ls: return ls[0][:42]
    return re.sub(r'<[^>]+>','',v).strip().split('\n')[0].strip()[:42]

IGNORE_APP = re.compile(r'mentionn|silhouette|couverture|hors-série|cameo', re.I)

def premier_chapitre(f):
    """Premier chapitre où le personnage apparaît vraiment.
    Le wiki liste aussi les mentions et silhouettes : on les saute quand
    elles sont annotées, sinon Hancock débuterait à Thriller Bark (« mentionnée »)
    au lieu d'Amazon Lily. Le chapitre 0 (one-shot prequel) est ignoré."""
    p = f.get("première", "")
    segments = re.split(r'<br\s*/?>|\n', p)
    nums = []
    for seg in segments:
        if IGNORE_APP.search(seg): continue
        nums += [int(n) for n in re.findall(r'\[\[Chapitre (\d+)', seg)]
    nums = [n for n in nums if n > 0]
    if not nums:   # repli : tout chapitre cité, annotations comprises
        nums = [int(n) for n in re.findall(r'\[\[Chapitre (\d+)', p) if int(n) > 0]
    return min(nums) if nums else None

def chapitre(wt):
    """Numéro du chapitre de première apparition, ou None si le personnage
    n'apparaît pas dans le manga (film, épisode filler, roman, spin-off)."""
    f=wiki.parse_fields(wt)
    m=re.search(r'\[\[Chapitre (\d+)', f.get("première",""))
    return int(m.group(1)) if m else None

def rang(nom, titre, wt):
    f=wiki.parse_fields(wt)
    ch=premier_chapitre(f)
    p=prime(f); h=wiki.get_height(f)
    return [nom, GENRE.get(titre,"?"), lien1(f.get("affiliation","")) or "Sans affiliation",
            camp(lien1(f.get("affiliation","")) or wiki.strip_wiki(f.get("occupation",""))),
            fruit(f), HAKI.get(titre,""), p if p is not None else -1, h if h is not None else -1,
            origine(f), arc(ch) if ch else "Inconnue"]

# --- notoriété -------------------------------------------------------------
# Le wiki recense jusqu'aux figurants d'une case. La longueur de la fiche est
# un bon indicateur : un personnage dont on connaît quelque chose a un article
# étoffé. Seuil calé sur les cas limites voulus (Buddle, 5132 caractères).
# Sont gardés d'office : les 238 personnages curés (ceux qui ont un emoji),
# quiconque a une prime, et les fiches à au moins 3 champs renseignés.
SEUIL_FICHE = 5000
esrc=open(ROOT+'js/emoji.js',encoding='utf-8').read()
EMOJI=set(json.loads(esrc[esrc.index('{'):esrc.rindex('}')+1]))

# Le wiki n'encode nulle part « le nom est donné dans l'œuvre » : ni catégorie,
# ni marqueur de source fiable (Koza porte la même référence Vivre Card qu'un
# figurant). La sélection a donc été faite à la main, une fois, et figée ici.
# Liste définitive triée à la main par l'utilisateur : un nom par ligne.
# C'est le seul filtre — rien d'autre n'entre, rien d'autre ne sort.
SELECTION = {l.strip() for l in open(ROOT+'tools/selection.txt',encoding='utf-8') if l.strip()}

def notable(nom, wt, r):
    return nom in SELECTION

rows=[]; vus=set(); ecartes=[]; obscurs=0
for nom, c in cures.items():                       # les 238 d'origine, sous leur nom curé
    titre=links.get(nom,nom)
    if nom not in SELECTION: continue
    rows.append(rang(nom,titre,c['wt'])); vus.add(titre)
for titre, wt in tous.items():                     # tout le reste du wiki
    if titre in vus or titre in cures: continue
    if re.search(r'\((homonymie|film|jeu|anime|non.?canon)\)',titre,re.I): ecartes.append(titre); continue
    if titre not in SELECTION: obscurs += 1; continue
    rows.append(rang(titre,titre,wt)); vus.add(titre)
manquants = SELECTION - {r[0] for r in rows}
print(f"hors sélection : {obscurs}")
if manquants: print("NON TROUVÉS :", sorted(manquants))

# Renommages : le wiki fr utilise parfois le vrai nom là où l'œuvre nous a fait
# connaître un surnom (amiraux, Baroque Works…). tools/renames.json fait foi.
# Renommages d'abord : tous les fichiers de correction ci-dessous
# désignent les personnages par leur nom final, celui affiché dans le jeu.
RENAMES = json.load(open(ROOT+'tools/renames.json'))
for r in rows:
    if r[0] in RENAMES: r[0] = RENAMES[r[0]]

# Certaines infobox n'ont pas de champ « affiliation » du tout : le groupe est
# alors fixé à la main d'après les catégories de la fiche.
AFFIL_FIX = {k: v for k, v in json.load(open(ROOT+'tools/affiliations.json')).items()
             if not k.startswith('_')}
for r in rows:
    if r[0] in AFFIL_FIX:
        r[2] = AFFIL_FIX[r[0]]
        # le camp suit l'affiliation corrigée, sauf si celle-ci ne désigne
        # aucun camp précis : on garde alors celui déduit de l'occupation
        # (« Famille Royale d'Erbaf » ne dit pas que Loki est un pirate)
        nouveau = camp(r[2])
        if nouveau != "Civil": r[3] = nouveau

# Les catégories Haki du wiki sont incomplètes : corrections manuelles.
HAKI_FIX = {k: v for k, v in json.load(open(ROOT+'tools/haki-fixes.json')).items()
            if not k.startswith('_')}
for r in rows:
    if r[0] in HAKI_FIX: r[5] = HAKI_FIX[r[0]]

# Le wiki écrit le même groupe de plusieurs façons : « Marine » / « Marines »,
# « Équipage de Big Mom » / « L'Équipage de Big Mom »… Deux membres du même
# camp ressortaient alors en rouge l'un contre l'autre. On regroupe les
# variantes et on retient l'orthographe la plus fréquente.
import unicodedata, collections
def _cle(a):
    a = unicodedata.normalize('NFD', a.lower()).encode('ascii','ignore').decode()
    a = re.sub(r"^(l')?(les |le |la |l')", '', a)
    a = re.sub(r'[^a-z0-9 ]', '', a).strip()
    a = re.sub(r's\b', '', a)
    return re.sub(r'\s+', ' ', a)

_freq = collections.Counter(r[2] for r in rows)
_groupes = collections.defaultdict(list)
for a in _freq: _groupes[_cle(a)].append(a)
_canon = {}
for variantes in _groupes.values():
    ref = max(variantes, key=lambda a: (_freq[a], -len(a)))
    for a in variantes: _canon[a] = ref
_fusions = sum(1 for a, r in _canon.items() if a != r)
for r in rows: r[2] = _canon[r[2]]
print(f"affiliations : {len(_freq)} libellés -> {len(_groupes)} groupes ({_fusions} variantes fusionnées)")

# les 10 membres d'origine partagent exactement la même affiliation
for r in rows:
    if r[0] in CORE: r[2], r[3] = CREW, "Pirate"

# exception canon : Gomu Gomu no Mi = Hito Hito no Mi modèle Nika (ch. 1044)
for r in rows:
    if r[0]=="Monkey D. Luffy": r[4]="Zoan Mythique"

rows.sort(key=lambda r: r[0].lower())
json.dump(rows, open('rows.json','w'), ensure_ascii=False)
print(f"total : {len(rows)}  (238 curés + {len(rows)-238} du wiki)")
for lbl,i,f in [("prime",6,lambda v:v>0),("taille",7,lambda v:v>0),("origine",8,lambda v:v!="Inconnue"),
                ("arc",9,lambda v:v!="Inconnue")]:
    print(f"  {lbl:8} connue : {sum(1 for r in rows if f(r[i])):>5}")
print(f"  haki     connu  : {sum(1 for r in rows if r[5]):>5}")
print(f"  fruit           : {sum(1 for r in rows if r[4]!='Aucun'):>5}")
