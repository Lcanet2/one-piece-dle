/* ================= ONE PIECE DLE — moteur de jeu ================= */
(function () {
"use strict";

/* ---------- 1. Construction des personnages ---------- */
const FIELDS = ["nom","genre","equipage","camp","fruit","haki","prime","taille","origine","arc"];

const CHARACTERS = RAW_CHARACTERS.map(r => {
  const c = {};
  FIELDS.forEach((f, i) => c[f] = r[i]);
  c.emoji = (typeof EMOJI !== "undefined" && EMOJI[c.nom]) || "";
  /* Le wiki recense ~1900 personnages, mais la plupart des figurants n'ont
     aucune donnée : ils resteraient indevinables en réponse du jour.
     Tout le monde est proposable ; seuls les personnages renseignés
     (ou pourvus d'un indice emoji) peuvent être la cible. */
  c.score = (c.prime > 0) + (c.taille > 0) + (c.haki !== "")
          + (c.fruit !== "Aucun") + (c.origine !== "Inconnue");
  c.estCible = c.emoji !== "" || c.score >= 2;
  c.arcIdx = ARCS.indexOf(c.arc);
  c.hakiSet = c.haki.split("").filter(Boolean);
  c.key = norm(c.nom);
  return c;
}).sort((a, b) => a.nom.localeCompare(b.nom, "fr"));

const BY_KEY = new Map(CHARACTERS.map(c => [c.key, c]));

/* alias / surnoms acceptés en saisie */
const ALIASES = {
  "luffy":"Monkey D. Luffy","mugiwara":"Monkey D. Luffy","chapeau de paille":"Monkey D. Luffy",
  "zoro":"Roronoa Zoro","zorro":"Roronoa Zoro","robin":"Nico Robin","chopper":"Tony Tony Chopper",
  "jinbei":"Jinbe","jimbei":"Jinbe","ace":"Portgas D. Ace","law":"Trafalgar D. Water Law",
  "trafalgar law":"Trafalgar D. Water Law","kid":"Eustass Kid","barbe blanche":"Barbe Blanche",
  "whitebeard":"Barbe Blanche","edward newgate":"Barbe Blanche","newgate":"Barbe Blanche",
  "blackbeard":"Barbe Noire","teach":"Barbe Noire","marshall d teach":"Barbe Noire",
  "big mom":"Big Mom","charlotte linlin":"Big Mom","linlin":"Big Mom",
  "roger":"Gol D. Roger","gold roger":"Gol D. Roger","rayleigh":"Silvers Rayleigh",
  "akainu":"Akainu","aokiji":"Aokiji","kizaru":"Kizaru","fujitora":"Fujitora","garp":"Monkey D. Garp",
  "dragon":"Monkey D. Dragon","mihawk":"Dracule Mihawk","oeil de faucon":"Dracule Mihawk",
  "doflamingo":"Donquixote Doflamingo","hancock":"Boa Hancock","moria":"Gecko Moria",
  "kuma":"Bartholomew Kuma","katakuri":"Charlotte Katakuri","cracker":"Charlotte Cracker",
  "smoothie":"Charlotte Smoothie","perospero":"Charlotte Perospero","pudding":"Charlotte Pudding",
  "brulee":"Charlotte Brulee","oden":"Kozuki Oden","momonosuke":"Kozuki Momonosuke",
  "momo":"Kozuki Momonosuke","hiyori":"Kozuki Hiyori","lucci":"Rob Lucci","vivi":"Nefeltari Vivi",
  "bon clay":"Mr. 2 Bon Clay","mr 2":"Mr. 2 Bon Clay","mr 3":"Galdino","mr 1":"Daz Bones",
  "pipo":"Usopp","pipeau":"Usopp","sogeking":"Usopp","sniper king":"Usopp",
  "baggy":"Buggy","chirurgien de la mort":"Trafalgar D. Water Law","cesar":"Caesar Clown",
  "cesar clown":"Caesar Clown","enel":"Enel","ener":"Enel","shirahoshi":"Shirahoshi",
  "sabo":"Sabo","ivankov":"Emporio Ivankov","iva":"Emporio Ivankov","kinemon":"Kin'emon",
  "shanks le roux":"Shanks","le roux":"Shanks","marco le phenix":"Marco","yamato":"Yamato",
  "kureha":"Dr. Kureha","hiluluk":"Dr. Hiluluk","saul":"Jaguar D. Saul","stussy":"Stussy",
  "saturn":"Saint Jaygarcia Saturn","imu":"Im","im sama":"Im",
  "don quichotte doflamingo":"Donquixote Doflamingo","doffy":"Donquixote Doflamingo",
  "zorro roronoa":"Roronoa Zoro","trafalgar law":"Trafalgar D. Water Law",
  "bentham":"Mr. 2 Bon Clay", "chadros higelyges":"Barbe Brune", "chess":"Smack", "dalton":"Dolton", "sakazuki":"Akainu", "borsalino":"Kizaru", "kuzan":"Aokiji", "issho":"Fujitora", "peeply lulu":"Lulu", "riku doldo iii":"Riku", "sterry":"Stelly"
};

function slug(name) {
  return name.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

/* Images locales optionnelles : dépose tes fichiers dans img/ puis lance
   tools/build-manifest.sh. Sans images, on retombe sur des pastilles colorées. */
const IMAGES = new Map();
function loadImages() {
  return fetch("img/manifest.json", { cache: "no-cache" })
    .then(r => r.ok ? r.json() : {})
    .then(m => { Object.entries(m).forEach(([k, v]) => IMAGES.set(k, "img/" + v)); })
    .catch(() => {});
}
function imgFor(c) { return IMAGES.get(slug(c.nom)) || null; }

function norm(s) {
  return s.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9 ]/g, "")
    .replace(/\s+/g, " ").trim();
}

/* les orthographes du wiki fr sont aussi acceptées ("Kaidou", "Ener", "Nefertari Vivi"…) */
const WIKI_ALIASES = new Map();
if (typeof WIKI_TITLES !== "undefined") {
  Object.entries(WIKI_TITLES).forEach(([mine, title]) => {
    const k = norm(title);
    if (!BY_KEY.has(k)) WIKI_ALIASES.set(k, mine);
  });
}

function findCharacter(input) {
  const n = norm(input);
  if (!n) return null;
  if (BY_KEY.has(n)) return BY_KEY.get(n);
  if (ALIASES[n]) return BY_KEY.get(norm(ALIASES[n])) || null;
  if (WIKI_ALIASES.has(n)) return BY_KEY.get(norm(WIKI_ALIASES.get(n))) || null;
  const starts = CHARACTERS.filter(c => c.key.startsWith(n));
  if (starts.length === 1) return starts[0];
  // dernier mot / sous-chaîne : "katakuri" -> Charlotte Katakuri
  const words = CHARACTERS.filter(c => c.key.split(" ").includes(n));
  if (words.length === 1) return words[0];
  const inside = CHARACTERS.filter(c => c.key.includes(n));
  if (inside.length === 1) return inside[0];
  return null;
}

/* ---------- 2. Modes ---------- */
const MODES = {
  classique: {
    label: "Classique",
    title: "Devine le personnage de One Piece du jour",
    sub: "Un nouveau mystère chaque jour. Tape le nom d'un personnage : les couleurs t'indiquent ce qui correspond.",
    answers: () => CHARACTERS.filter(c => c.estCible),
    maxTries: Infinity
  },
  emoji: {
    label: "Emoji",
    title: "Quel personnage se cache derrière ces emojis ?",
    sub: "Trois indices en emoji. Chaque mauvaise réponse t'en révèle un peu plus sur le personnage.",
    answers: () => CHARACTERS.filter(c => c.emoji.length > 0),
    maxTries: Infinity
  },
  prime: {
    label: "Prime",
    title: "À qui appartient cette prime ?",
    sub: "Une prime, un pirate. Le tableau t'aide à recouper les indices.",
    answers: () => CHARACTERS.filter(c => c.estCible && c.prime > 1000),
    maxTries: Infinity
  }
};

/* ---------- 3. Colonnes du tableau ---------- */
const HAKI = {
  A: { emoji: '<span class="hk-arm">💪</span>', nom: "Armement" },
  O: { emoji: "👁️", nom: "Observation" },
  R: { emoji: "👑", nom: "Rois" }
};

const COLUMNS = [
  { key: "nom",      label: "Personnage", type: "name" },
  { key: "genre",    label: "Genre",      type: "exact",  fmt: v => ({M:"Homme",F:"Femme","?":"Inconnu"}[v] || v) },
  { key: "equipage", label: "Affiliation",type: "affil" },
  { key: "fruit",    label: "Fruit du Démon", type: "fruit" },
  { key: "haki",     label: "Haki",       type: "set" },
  { key: "prime",    label: "Prime",      type: "num", fmt: fmtBounty, zeroSiInconnu: true },
  { key: "taille",   label: "Taille",     type: "num", fmt: v => v < 0 ? "?" : (v >= 100 ? (v/100).toFixed(2).replace(".", ",") + " m" : v + " cm") },
  { key: "arcIdx",   label: "1re apparition", type: "num", fmt: v => ARCS[v] || "?" }
];

function fmtBounty(v) {
  // pas de prime (inconnue ou inexistante) : 0 suivi du symbole berry
  if (v <= 0) return "0\u0E3F";
  if (v >= 1e9) return (v / 1e9).toFixed(3).replace(/0+$/, "").replace(/\.$/, "").replace(".", ",") + " Md";
  if (v >= 1e6) return (v / 1e6).toFixed(0) + " M";
  return v.toLocaleString("fr-FR");
}

/* ---------- 4. Comparaison ---------- */
function compareField(col, guess, target) {
  const gv = guess[col.key], tv = target[col.key];

  switch (col.type) {
    case "name":
      return { state: guess.nom === target.nom ? "ok" : "no", text: guess.nom };

    case "exact":
      return { state: gv === tv ? "ok" : "no", text: col.fmt ? col.fmt(gv) : gv };

    case "affil":
      // pas de "pas loin" ici : deux pirates d'équipages sans rapport
      // ressortaient en jaune, ce qui induisait en erreur
      return { state: gv === tv ? "ok" : "no", text: gv };

    case "fruit": {
      let state = "no";
      if (gv === tv) state = "ok";
      else if (gv.includes("Zoan") && tv.includes("Zoan")) state = "mid";
      else if (gv !== "Aucun" && tv !== "Aucun") state = "mid";
      return { state, text: gv };
    }

    case "set": {
      const g = guess.hakiSet, t = target.hakiSet;
      const txt  = g.length ? g.map(x => HAKI[x].emoji).join(" ") : "—";
      const aria = g.length ? g.map(x => HAKI[x].nom).join(" + ") : "Aucun";
      const inter = g.filter(x => t.includes(x));
      let state = "no";
      if (g.length === t.length && inter.length === g.length) state = "ok";
      else if (inter.length > 0) state = "mid";
      return { state, text: txt, aria, cls: "haki" };
    }

    case "num": {
      const text = col.fmt ? col.fmt(gv) : String(gv);
      // Une prime non révélée s'affiche « 0฿ » : elle se compare donc comme un
      // zéro, sinon la colonne restait sans flèche dès que le personnage
      // mystère n'avait pas de prime connue.
      const g = col.zeroSiInconnu ? Math.max(0, gv) : gv;
      const t = col.zeroSiInconnu ? Math.max(0, tv) : tv;
      if (g < 0 || t < 0) return { state: g === t ? "ok" : "no", text, arrow: "" };
      if (g === t) return { state: "ok", text, arrow: "" };
      const close = col.key === "taille" ? Math.abs(g - t) <= 15
                  : col.key === "prime"  ? (Math.max(g, t) > 0 && Math.abs(g - t) / Math.max(g, t) <= 0.2)
                  : Math.abs(g - t) === 1;
      return { state: close ? "mid" : "no", text, arrow: g < t ? "⬆" : "⬇" };
    }
  }
  return { state: "no", text: String(gv) };
}

/* ---------- 5. Sélection du personnage du jour ---------- */
function hash32(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}
function todayKey(offset) {
  const d = new Date();
  d.setDate(d.getDate() + (offset || 0));
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}
function dailyCharacter(mode, offset) {
  const pool = MODES[mode].answers();
  return pool[hash32("onepiecedle|" + mode + "|" + todayKey(offset)) % pool.length];
}
/* ---------- 6. Stockage ---------- */
const STORE = "onepiecedle.v1";
function loadStore() {
  try { return JSON.parse(localStorage.getItem(STORE)) || {}; } catch (e) { return {}; }
}
function saveStore(s) {
  try { localStorage.setItem(STORE, JSON.stringify(s)); } catch (e) {}
}
function stats(mode) {
  const s = loadStore();
  s.stats = s.stats || {};
  s.stats[mode] = s.stats[mode] || { played: 0, wins: 0, streak: 0, best: 0, totalTries: 0 };
  return s.stats[mode];
}
/* Progression du jour, par mode. Repartie à zéro dès que la date change. */
function cleDuJour() { return todayKey(state.dayOffset); }

/* Une entrée par mode ET par jour : rejouer un jour passé ne doit pas
   écraser la partie d'un autre jour. */
function cleProgression() { return state.mode + "|" + cleDuJour(); }

function loadProgress() {
  return (loadStore().progress || {})[cleProgression()] || null;
}
function saveProgress() {
  const s = loadStore();
  s.progress = s.progress || {};
  // purge de tout ce qui sort de la fenêtre rejouable
  const valides = [];
  for (let i = 0; i < JOURS_REJOUABLES; i++) valides.push(todayKey(-i));
  Object.keys(s.progress).forEach(k => {
    if (!valides.includes(k.split("|")[1])) delete s.progress[k];
  });
  s.progress[cleProgression()] = {
    guesses: state.guesses.map(g => g.nom),
    finished: state.finished
  };
  saveStore(s);
}

function recordWin(mode, tries) {
  const s = loadStore();
  const st = stats(mode);
  st.played++; st.wins++; st.streak++; st.totalTries += tries;
  st.best = Math.max(st.best, st.streak);
  s.stats = s.stats || {}; s.stats[mode] = st;
  saveStore(s);
}

/* ---------- 7. État ---------- */
const JOURS_REJOUABLES = 7;   // aujourd'hui + les 6 jours précédents

const state = {
  mode: "classique",
  dayOffset: 0,               // 0 = aujourd'hui, -1 = hier…
  target: null,
  guesses: [],
  finished: false
};

/* ---------- 8. DOM ---------- */
const $ = id => document.getElementById(id);
const el = {
  modes: $("modes"), heroTitle: $("hero-title"), heroSub: $("hero-sub"),
  clue: $("clue"), input: $("guess-input"), btn: $("guess-btn"),
  sug: $("suggestions"), tryCount: $("try-count"), poolCount: $("pool-count"),
  result: $("result"), boardHead: $("board-head"), board: $("board"),
  hints: $("hints"), hintGrid: $("hint-grid"),
  modal: $("modal"), modalBody: $("modal-body"), modalX: $("modal-x"),
  dayPrev: $("day-prev"), dayNext: $("day-next"), dayText: $("day-text"),
  dayNav: document.querySelector(".day-nav")
};

/* ---------- 9. Rendu ---------- */
/* Symboles d'état : redondants avec la couleur, pour les daltoniens */
const MARKS = {
  ok:  '<svg viewBox="0 0 20 20" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 10.5l4 4 8-9"/></svg>',
  mid: '<svg viewBox="0 0 20 20" fill="none" stroke="#2b1d00" stroke-width="3" stroke-linecap="round" aria-hidden="true"><path d="M3 7.5c2-2.5 4-2.5 6 0s4 2.5 6 0"/><path d="M3 13.5c2-2.5 4-2.5 6 0s4 2.5 6 0"/></svg>',
  no:  '<svg viewBox="0 0 20 20" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg>'
};
const MARK_LABEL = { ok: "exact", mid: "partiel", no: "faux" };

function renderHead() {
  el.boardHead.innerHTML = COLUMNS.map(c => `<div>${c.label}</div>`).join("");
}

function avatarColor(name) {
  const h = hash32(name) % 360;
  return `hsl(${h} 70% 62%)`;
}

function avatarHTML(c, cls) {
  const src = imgFor(c);
  return src
    ? `<img class="${cls} av-img" src="${src}" alt="" loading="lazy">`
    : `<span class="${cls}" style="background:${avatarColor(c.nom)}">${c.nom[0]}</span>`;
}

function renderGuess(guess, instant) {
  const row = document.createElement("div");
  row.className = "row" + (instant ? " no-anim" : "");
  COLUMNS.forEach((col, i) => {
    const r = compareField(col, guess, state.target);
    const cell = document.createElement("div");
    cell.className = "cell " + (col.type === "name" ? "name" : r.state) + (r.cls ? " " + r.cls : "");
    if (r.aria) cell.title = r.aria;
    if (!instant) cell.style.animationDelay = (i * 90) + "ms";
    if (col.type !== "name") {
      cell.setAttribute("role", "img");
      cell.setAttribute("aria-label",
        `${col.label} : ${r.aria || r.text}, ${MARK_LABEL[r.state]}` +
        (r.arrow === "⬆" ? ", plus grand" : r.arrow === "⬇" ? ", plus petit" : ""));
    }
    cell.innerHTML = (col.type !== "name" ? `<span class="mark">${MARKS[r.state]}</span>` : "")
      + (r.arrow ? `<span class="arrow">${r.arrow}</span>` : "")
      + (col.type === "name" ? avatarHTML(guess, "cell-av") : "")
      + `<span>${r.text}</span>`;
    row.appendChild(cell);
  });
  el.board.appendChild(row);
}

function renderClue() {
  const t = state.target;
  if (state.mode === "emoji") {
    el.clue.hidden = false;
    el.clue.innerHTML =
      `<div class="clue-label">Indice emoji</div>
       <div class="clue-emoji">${t.emoji}</div>
       <div class="clue-extra">${state.guesses.length >= 3 ? "Affiliation : " + t.equipage : "3 essais pour débloquer un indice"}</div>`;
  } else if (state.mode === "prime") {
    el.clue.hidden = false;
    el.clue.innerHTML =
      `<div class="clue-label">Prime recherchée</div>
       <div class="clue-bounty">${t.prime.toLocaleString("fr-FR")} <span style="font-size:.5em">berries</span></div>
       <div class="clue-extra">${state.guesses.length >= 3 ? "Origine : " + t.origine : "3 essais pour débloquer un indice"}</div>`;
  } else {
    el.clue.hidden = true;
    el.clue.innerHTML = "";
  }
}

const HINT_STEPS = [
  { at: 4,  label: "Origine",     get: t => t.origine },
  { at: 6,  label: "Camp",        get: t => t.camp },
  { at: 8,  label: "Première apparition", get: t => t.arc },
  { at: 10, label: "Initiale",    get: t => t.nom[0].toUpperCase() + "…" }
];

function renderHints() {
  const n = state.guesses.length;
  if (n === 0) { el.hints.hidden = true; return; }
  el.hints.hidden = false;
  el.hintGrid.innerHTML = HINT_STEPS.map(h => {
    const open = n >= h.at || state.finished;
    return `<div class="hint ${open ? "" : "locked"}">
              <b>${h.label}</b>${open ? h.get(state.target) : "Verrouillé — " + h.at + " essais"}
            </div>`;
  }).join("");
}

function renderDay() {
  const j = state.dayOffset;
  el.dayText.textContent = j === 0 ? "Défi du jour"
    : new Date(Date.now() + j * 86400000).toLocaleDateString("fr-FR",
        { weekday: "long", day: "numeric", month: "long" });
  el.dayPrev.disabled = j <= -(JOURS_REJOUABLES - 1);
  el.dayNext.disabled = j >= 0;
  if (el.dayNav) el.dayNav.classList.toggle("passe", j < 0);
}

function renderCounters() {
  el.tryCount.textContent = state.guesses.length;
  el.poolCount.textContent = CHARACTERS.length;
}

function shareText() {
  const lines = state.guesses.map(g =>
    COLUMNS.slice(1).map(c => ({ ok: "🟩", mid: "🟨", no: "🟥" }[compareField(c, g, state.target).state])).join("")
  );
  return `OnePieceDle — ${MODES[state.mode].label} ${cleDuJour()}\n` +
         `${state.guesses.length} essai(s)\n` + lines.join("\n");
}

function msUntilMidnight() {
  const now = new Date();
  const next = new Date(now);
  next.setHours(24, 0, 0, 0);
  return next - now;
}
function fmtDuration(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60]
    .map(n => String(n).padStart(2, "0")).join(":");
}

let countdownTimer = null;
function renderResult(won) {
  el.result.hidden = false;
  const t = state.target;
  el.result.innerHTML = `
    <h2 class="${won ? "win" : "lose"}">${won ? "Trouvé !" : "Perdu"}</h2>
    <p>Le personnage était <strong>${t.nom}</strong> — ${t.equipage}${t.prime > 0 ? " · prime de " + t.prime.toLocaleString("fr-FR") + " berries" : ""}.
       ${won ? "Résolu en <strong>" + state.guesses.length + "</strong> essai(s)." : ""}</p>
    ${state.dayOffset === 0 ? `<p>Prochain personnage dans <span class="countdown" id="cd">--:--:--</span></p>` : `<p>Partie rejouée — les statistiques ne sont pas comptées.</p>`}
    ${wikiLink(t)}
    <div class="actions">
      <button class="primary" id="btn-share"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8.5" y="3.5" width="11" height="14" rx="2"/><path d="M15.5 20.5h-9a2 2 0 0 1-2-2v-11"/></svg><span>Partager</span></button>
    </div>`;

  $("btn-share").onclick = () => {
    const txt = shareText();
    (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject())
      .then(() => toast("Résultat copié !"))
      .catch(() => toast("Copie impossible sur ce navigateur"));
  };
  clearInterval(countdownTimer);
  if (state.dayOffset === 0) {          // le compte à rebours n'a de sens qu'aujourd'hui
    const tick = () => { const c = $("cd"); if (c) c.textContent = fmtDuration(msUntilMidnight()); };
    tick(); countdownTimer = setInterval(tick, 1000);
  }
}

function wikiLink(c) {
  const t = (typeof WIKI_TITLES !== "undefined") && WIKI_TITLES[c.nom];
  if (!t) return "";
  const url = "https://onepiece.fandom.com/fr/wiki/" + encodeURIComponent(t.replace(/ /g, "_"));
  return `<p class="wiki-link"><a href="${url}" target="_blank" rel="noopener"><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2 2 0 0 1 6 4h5v15H6a2 2 0 0 0-2 1.5z"/><path d="M20 5.5A2 2 0 0 0 18 4h-5v15h5a2 2 0 0 1 2 1.5z"/></svg><span>Voir la fiche sur One Piece Encyclopédie</span></a></p>`;
}

function toast(msg) {
  const d = document.createElement("div");
  d.className = "toast"; d.textContent = msg;
  document.body.appendChild(d);
  setTimeout(() => d.remove(), 2200);
}

/* ---------- 10. Boucle de jeu ---------- */
function newGame() {
  state.target = dailyCharacter(state.mode, state.dayOffset);
  state.guesses = [];
  state.finished = false;
  el.board.innerHTML = "";
  el.result.hidden = true;
  el.input.value = "";
  el.input.disabled = false;
  el.btn.disabled = false;
  hideSuggestions();
  renderHead();
  renderDay();

  // rejoue la partie du jour si elle est déjà entamée
  const saved = loadProgress();
  if (saved) {
    saved.guesses.forEach(nom => {
      const c = BY_KEY.get(norm(nom));
      if (c) { state.guesses.push(c); renderGuess(c, true); }
    });
    if (saved.finished && state.guesses.some(g => g.nom === state.target.nom)) {
      state.finished = true;
      el.input.disabled = true;
      el.btn.disabled = true;
      renderResult(true);
    }
  }

  renderClue();
  renderHints();
  renderCounters();
}

function submitGuess(raw) {
  if (state.finished) return;
  const c = findCharacter(raw);
  if (!c) { toast("Personnage inconnu 🤔"); return; }
  if (state.guesses.some(g => g.nom === c.nom)) { toast("Déjà proposé !"); return; }

  state.guesses.push(c);
  renderGuess(c);
  renderClue();
  renderHints();
  renderCounters();
  el.input.value = "";
  hideSuggestions();

  if (c.nom === state.target.nom) {
    state.finished = true;
    el.input.disabled = true;
    el.btn.disabled = true;
    if (state.dayOffset === 0) recordWin(state.mode, state.guesses.length);
    setTimeout(() => renderResult(true), 700);
  }
  saveProgress();
}

/* ---------- 11. Autocomplétion ---------- */
let sugIndex = -1;
function showSuggestions(q) {
  const n = norm(q);
  if (!n) return hideSuggestions();
  const pool = CHARACTERS.filter(c => !state.guesses.some(g => g.nom === c.nom));
  const starts = pool.filter(c => c.key.startsWith(n));
  const contains = pool.filter(c => !c.key.startsWith(n) && c.key.includes(n));
  const list = starts.concat(contains).slice(0, 8);
  if (!list.length) return hideSuggestions();

  sugIndex = -1;
  el.sug.hidden = false;
  el.sug.innerHTML = list.map((c, i) => `
    <li data-name="${c.nom.replace(/"/g, "&quot;")}" data-i="${i}">
      ${avatarHTML(c, "sug-av")}
      <span>${c.nom}</span>
      <span class="sug-badge">${c.equipage}</span>
    </li>`).join("");

  el.sug.querySelectorAll("li").forEach(li => {
    li.onmousedown = e => { e.preventDefault(); submitGuess(li.dataset.name); };
  });
}
function hideSuggestions() { el.sug.hidden = true; el.sug.innerHTML = ""; sugIndex = -1; }

function moveSug(delta) {
  const items = [...el.sug.querySelectorAll("li")];
  if (!items.length) return;
  sugIndex = (sugIndex + delta + items.length) % items.length;
  items.forEach((li, i) => li.classList.toggle("sel", i === sugIndex));
  items[sugIndex].scrollIntoView({ block: "nearest" });
}

/* ---------- 12. Modales ---------- */
function openModal(html) { el.modalBody.innerHTML = html; el.modal.hidden = false; }
function closeModal() { el.modal.hidden = true; el.modalBody.innerHTML = ""; }

const HELP_HTML = `
  <h2>Comment jouer ?</h2>
  <p>Devine le personnage mystère de One Piece. À chaque proposition, chaque case se colore selon sa correspondance avec le personnage recherché.</p>
  <h3>Les couleurs</h3>
  <div class="ex"><i style="background:#38c162"></i> Vert : la valeur est exactement la bonne.</div>
  <div class="ex"><i style="background:#e0a92b"></i> Jaune : c'est proche (même camp, même famille de Fruit du Démon, un Haki en commun, prime ou taille voisine).</div>
  <div class="ex"><i style="background:#55688c"></i> Gris : aucun rapport.</div>
  <h3>Le Haki</h3>
  <p><span class="hk-arm">💪</span> Armement · 👁️ Observation · 👑 Rois · — aucun Haki connu.
     Vert si les types correspondent exactement, jaune s'il y en a au moins un en commun.</p>
  <h3>Les flèches</h3>
  <p><strong>⬆</strong> la valeur recherchée est plus grande que ta proposition, <strong>⬇</strong> elle est plus petite. Valable pour la prime, la taille et la saga de première apparition.</p>
  <h3>Les modes</h3>
  <ul>
    <li><strong>Classique</strong> — tout le roster, uniquement le tableau d'indices.</li>
    <li><strong>Emoji</strong> — un personnage résumé en emojis.</li>
    <li><strong>Prime</strong> — retrouve à qui appartient une prime donnée.</li>
  </ul>
  <p>Chaque mode propose <strong>un personnage par jour</strong>, le même pour tout le monde jusqu'à minuit.</p>`;

function statsHTML() {
  const st = stats(state.mode);
  const avg = st.wins ? (st.totalTries / st.wins).toFixed(1).replace(".", ",") : "—";
  return `
    <h2>Statistiques — ${MODES[state.mode].label}</h2>
    <div class="stat-row">
      <div class="stat"><b>${st.played}</b><span>Parties</span></div>
      <div class="stat"><b>${st.wins}</b><span>Victoires</span></div>
      <div class="stat"><b>${st.streak}</b><span>Série</span></div>
      <div class="stat"><b>${st.best}</b><span>Record</span></div>
      <div class="stat"><b>${avg}</b><span>Essais moy.</span></div>
    </div>
    <p style="text-align:center">${CHARACTERS.length} personnages dans la base.</p>`;
}

/* ---------- 13. Événements ---------- */
el.modes.addEventListener("click", e => {
  const b = e.target.closest(".mode-btn");
  if (!b) return;
  [...el.modes.children].forEach(x => x.classList.remove("is-active"));
  b.classList.add("is-active");
  state.mode = b.dataset.mode;
  el.heroTitle.textContent = MODES[state.mode].title;
  el.heroSub.textContent = MODES[state.mode].sub;
  newGame();
});

el.dayPrev.onclick = () => {
  if (state.dayOffset > -(JOURS_REJOUABLES - 1)) { state.dayOffset--; newGame(); }
};
el.dayNext.onclick = () => {
  if (state.dayOffset < 0) { state.dayOffset++; newGame(); }
};

el.btn.onclick = () => {
  const items = [...el.sug.querySelectorAll("li")];
  if (sugIndex >= 0 && items[sugIndex]) submitGuess(items[sugIndex].dataset.name);
  else submitGuess(el.input.value);
};

el.input.addEventListener("input", () => showSuggestions(el.input.value));
el.input.addEventListener("blur", () => setTimeout(hideSuggestions, 120));
el.input.addEventListener("keydown", e => {
  if (e.key === "ArrowDown") { e.preventDefault(); moveSug(1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); moveSug(-1); }
  else if (e.key === "Escape") hideSuggestions();
  else if (e.key === "Enter") {
    e.preventDefault();
    const items = [...el.sug.querySelectorAll("li")];
    if (sugIndex >= 0 && items[sugIndex]) submitGuess(items[sugIndex].dataset.name);
    else submitGuess(el.input.value);
  }
});

$("btn-help").onclick = () => openModal(HELP_HTML);
$("btn-stats").onclick = () => openModal(statsHTML());
el.modalX.onclick = closeModal;
el.modal.addEventListener("click", e => { if (e.target === el.modal) closeModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

/* ---------- 14. Démarrage ---------- */
newGame();
loadImages().then(newGame);   // redessine le plateau avec les portraits
el.input.focus();

/* debug */
window.OPD = { CHARACTERS, MODES, state, findCharacter, compareField, COLUMNS, submitGuess, newGame };
})();
