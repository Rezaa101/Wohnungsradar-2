"""Erzeugt das statische Dashboard (docs/index.html)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wohnungsradar</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  --beton:#E4E8EB; --karte:#FFFFFF; --tinte:#11161B; --grau:#69747E;
  --linie:#CFD6DC; --signal:#1F4EE8; --alarm:#A81E32;
  --p-kleinanzeigen:#2E9E5B; --p-immoscout24:#E2681C;
  --p-wg-gesucht:#7A3FC4; --p-immowelt:#0F7C8C;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--beton); color:var(--tinte);
  font:400 15px/1.5 Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 80px}

/* ---------- Kopf ---------- */
header{padding:28px 0 18px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
.wortmarke{font:800 30px/0.9 Archivo,sans-serif;letter-spacing:-0.035em;text-transform:uppercase;margin:0}
.wortmarke span{color:var(--signal)}
.stand{font:500 12px/1.4 'JetBrains Mono',monospace;color:var(--grau);text-align:right}
.stand b{display:block;font-weight:700;font-size:19px;color:var(--tinte)}

/* ---------- Puls ---------- */
.puls{background:var(--karte);border:1px solid var(--linie);padding:14px 16px 10px;margin-bottom:14px}
.puls-titel{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--grau);margin-bottom:12px}
.balken{display:flex;align-items:flex-end;gap:2px;height:44px}
.balken i{flex:1;background:var(--linie);min-height:2px;display:block;transition:height .3s}
.balken i.aktiv{background:var(--signal)}
.puls-achse{display:flex;justify-content:space-between;font:400 10px/1 'JetBrains Mono',monospace;color:var(--grau);margin-top:6px}

/* ---------- Filter ---------- */
.filter{background:var(--karte);border:1px solid var(--linie);padding:14px 16px;margin-bottom:14px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.chip{font:500 12px/1 'JetBrains Mono',monospace;padding:7px 11px;border:1px solid var(--linie);background:transparent;color:var(--grau);cursor:pointer;text-transform:uppercase;letter-spacing:.06em}
.chip[aria-pressed="true"]{border-color:var(--tinte);color:var(--tinte);background:#F3F5F7}
.chip[aria-pressed="true"]::before{content:"";display:inline-block;width:7px;height:7px;background:currentColor;margin-right:7px;vertical-align:middle}
.chip.k[aria-pressed="true"]{color:var(--p-kleinanzeigen);border-color:var(--p-kleinanzeigen)}
.chip.i[aria-pressed="true"]{color:var(--p-immoscout24);border-color:var(--p-immoscout24)}
.chip.w[aria-pressed="true"]{color:var(--p-wg-gesucht);border-color:var(--p-wg-gesucht)}
.chip.o[aria-pressed="true"]{color:var(--p-immowelt);border-color:var(--p-immowelt)}
.feld{display:flex;align-items:center;gap:6px;font:500 11px/1 'JetBrains Mono',monospace;color:var(--grau);text-transform:uppercase;letter-spacing:.06em}
.feld input,.feld select{font:500 13px/1 'JetBrains Mono',monospace;padding:7px 8px;border:1px solid var(--linie);background:var(--karte);color:var(--tinte);width:92px}
.feld input#suchtext{width:150px}
:focus-visible{outline:2px solid var(--signal);outline-offset:2px}

/* ---------- Liste ---------- */
.zeile{display:grid;grid-template-columns:4px 1fr auto;background:var(--karte);border:1px solid var(--linie);border-top:none;text-decoration:none;color:inherit}
.liste .zeile:first-child{border-top:1px solid var(--linie)}
.zeile:hover{background:#F3F5F7}
.zeile:hover .titel{color:var(--signal)}
.rail{background:var(--linie)}
.zeile[data-p="kleinanzeigen"] .rail{background:var(--p-kleinanzeigen)}
.zeile[data-p="immoscout24"] .rail{background:var(--p-immoscout24)}
.zeile[data-p="wg-gesucht"] .rail{background:var(--p-wg-gesucht)}
.zeile[data-p="immowelt"] .rail{background:var(--p-immowelt)}
.mitte{padding:13px 16px;min-width:0}
.titel{font:600 15px/1.35 Inter,sans-serif;margin:0 0 5px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.fakten{font:500 13px/1 'JetBrains Mono',monospace;color:var(--tinte);display:flex;flex-wrap:wrap;gap:14px}
.fakten .leer{color:var(--linie)}
.fakten .qm{color:var(--grau)}
.ort{font:400 12px/1.3 Inter,sans-serif;color:var(--grau);margin-top:6px}
.ort b{font-weight:600;color:var(--tinte)}
.feld select{width:auto;min-width:96px}
.rechts{padding:13px 16px;text-align:right;white-space:nowrap;display:flex;flex-direction:column;justify-content:center;gap:6px}
.alter{font:500 12px/1 'JetBrains Mono',monospace;color:var(--grau)}
.neu{font:700 10px/1 'JetBrains Mono',monospace;letter-spacing:.1em;color:var(--karte);background:var(--signal);padding:4px 6px;align-self:flex-end}
.zeile.alt{opacity:.62}

/* ---------- Quellen & Leerzustand ---------- */
.quellen{margin-top:26px;background:var(--karte);border:1px solid var(--linie);padding:14px 16px}
.quellen summary{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--grau);cursor:pointer}
.quelle{display:flex;gap:10px;align-items:baseline;padding:9px 0;border-bottom:1px solid var(--linie);font:400 13px/1.4 Inter,sans-serif}
.quelle:last-child{border-bottom:none}
.quelle .status{font:700 10px/1 'JetBrains Mono',monospace;letter-spacing:.08em;padding:4px 6px;flex-shrink:0}
.status.ok{background:#E6F2EA;color:#1D6B3F}
.status.fehler{background:#F7E4E7;color:var(--alarm)}
.quelle .hinweis{color:var(--grau);font-size:12px}
.leerzustand{background:var(--karte);border:1px solid var(--linie);padding:44px 20px;text-align:center}
.leerzustand p{margin:0 0 6px;font:600 16px Inter,sans-serif}
.leerzustand small{color:var(--grau)}
footer{margin-top:22px;font:400 11px/1.6 'JetBrains Mono',monospace;color:var(--grau)}

@media (max-width:640px){
  .wortmarke{font-size:23px}
  .zeile{grid-template-columns:4px 1fr}
  .rechts{grid-column:2;flex-direction:row;align-items:center;justify-content:flex-start;padding:0 16px 13px}
  .neu{align-self:auto}
  .feld input,.feld select{width:78px}
  .feld input#suchtext{width:100%}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1 class="wortmarke">Wohnungs<span>radar</span></h1>
  <div class="stand"><b id="anzahl">—</b>Treffer · Stand __STAND__</div>
</header>

<section class="puls">
  <div class="puls-titel">Neue Anzeigen pro Stunde · letzte 24 h</div>
  <div class="balken" id="puls" aria-hidden="true"></div>
  <div class="puls-achse"><span>vor 24 h</span><span>jetzt</span></div>
</section>

<section class="filter">
  <button class="chip k" data-plattform="kleinanzeigen" aria-pressed="true">Kleinanzeigen</button>
  <button class="chip i" data-plattform="immoscout24" aria-pressed="true">ImmoScout24</button>
  <button class="chip w" data-plattform="wg-gesucht" aria-pressed="true">WG-Gesucht</button>
  <button class="chip o" data-plattform="immowelt" aria-pressed="true">Immowelt</button>
  <label class="feld" id="stadtfeld" hidden>Stadt<select id="stadt"><option value="">alle</option></select></label>
  <label class="feld">max €<input type="number" id="maxpreis" step="50" placeholder="—"></label>
  <label class="feld">ab Zi.<input type="number" id="minzimmer" step="0.5" placeholder="—"></label>
  <label class="feld">ab m²<input type="number" id="minflaeche" step="5" placeholder="—"></label>
  <label class="feld">Suche<input type="search" id="suchtext" placeholder="Stichwort"></label>
  <button class="chip" id="nurneu" aria-pressed="false">nur 24 h</button>
</section>

<div class="liste" id="liste"></div>

<details class="quellen" __QUELLEN_OFFEN__>
  <summary>Quellen (__QUELLEN_ZAHL__) · __FEHLER_ZAHL__ mit Problemen</summary>
  <div>__QUELLEN__</div>
</details>

<footer>Aktualisierung alle __TAKT__ Minuten zwischen 8 und 22 Uhr über GitHub Actions · nächster Lauf richtet sich nach der Auslastung der Runner</footer>
</div>

<script>
const ANZEIGEN = __DATEN__;
const jetzt = Date.now();
const el = (id) => document.getElementById(id);

function alterText(ms){
  const min = Math.round(ms/60000);
  if (min < 1) return "gerade eben";
  if (min < 60) return "vor " + min + " Min";
  const std = Math.round(min/60);
  if (std < 24) return "vor " + std + " Std";
  return "vor " + Math.round(std/24) + " Tg";
}
const eur = (n) => n == null ? null : n.toLocaleString("de-DE", {maximumFractionDigits:0}) + " €";

function zeichnePuls(daten){
  const eimer = new Array(24).fill(0);
  daten.forEach(a => {
    const std = Math.floor((jetzt - new Date(a.gefunden_am).getTime())/3600000);
    if (std >= 0 && std < 24) eimer[23-std]++;
  });
  const max = Math.max(1, ...eimer);
  el("puls").innerHTML = eimer.map((n,i) =>
    `<i class="${n>0?'aktiv':''}" style="height:${Math.max(2, n/max*44)}px" title="${n} vor ${23-i} Std"></i>`
  ).join("");
}

function zeichneListe(){
  const aktive = [...document.querySelectorAll(".chip[data-plattform]")]
    .filter(c => c.getAttribute("aria-pressed") === "true")
    .map(c => c.dataset.plattform);
  const maxPreis = parseFloat(el("maxpreis").value) || Infinity;
  const minZimmer = parseFloat(el("minzimmer").value) || 0;
  const minFlaeche = parseFloat(el("minflaeche").value) || 0;
  const text = el("suchtext").value.trim().toLowerCase();
  const nurNeu = el("nurneu").getAttribute("aria-pressed") === "true";
  const stadt = el("stadt").value;

  const gefiltert = ANZEIGEN.filter(a => {
    const alter = jetzt - new Date(a.gefunden_am).getTime();
    if (!aktive.includes(a.plattform)) return false;
    if (stadt && a.stadt !== stadt) return false;
    if (a.preis != null && a.preis > maxPreis) return false;
    if (minZimmer && (a.zimmer == null || a.zimmer < minZimmer)) return false;
    if (minFlaeche && (a.flaeche == null || a.flaeche < minFlaeche)) return false;
    if (text && !((a.titel + " " + a.ort + " " + (a.stadt||"")).toLowerCase().includes(text))) return false;
    if (nurNeu && alter > 86400000) return false;
    return true;
  }).sort((a,b) => new Date(b.gefunden_am) - new Date(a.gefunden_am));

  el("anzahl").textContent = gefiltert.length;
  zeichnePuls(gefiltert);

  if (!gefiltert.length){
    el("liste").innerHTML = `<div class="leerzustand"><p>Keine Treffer für diese Filter.</p>
      <small>Filter weiter stellen oder unten prüfen, ob eine Quelle geblockt wurde.</small></div>`;
    return;
  }

  el("liste").innerHTML = gefiltert.map(a => {
    const alter = jetzt - new Date(a.gefunden_am).getTime();
    const frisch = alter < 3600000;
    const qm = (a.preis && a.flaeche) ? (a.preis/a.flaeche).toFixed(1).replace(".", ",") + " €/m²" : "";
    return `<a class="zeile ${alter > 172800000 ? 'alt' : ''}" data-p="${a.plattform}" href="${a.url}" target="_blank" rel="noopener">
      <div class="rail"></div>
      <div class="mitte">
        <div class="titel">${a.titel || "Ohne Titel"}</div>
        <div class="fakten">
          <span class="${a.preis==null?'leer':''}">${eur(a.preis) || "Preis k. A."}</span>
          <span class="${a.zimmer==null?'leer':''}">${a.zimmer ? String(a.zimmer).replace(".", ",") + " Zi." : "– Zi."}</span>
          <span class="${a.flaeche==null?'leer':''}">${a.flaeche ? String(a.flaeche).replace(".", ",") + " m²" : "– m²"}</span>
          ${qm ? `<span class="qm">${qm}</span>` : ""}
        </div>
        ${(a.stadt || a.ort) ? `<div class="ort">${a.stadt ? `<b>${a.stadt}</b>` : ""}${a.stadt && a.ort ? " · " : ""}${a.ort || ""}</div>` : ""}
      </div>
      <div class="rechts">
        ${frisch ? '<span class="neu">NEU</span>' : ""}
        <span class="alter">${alterText(alter)}</span>
      </div>
    </a>`;
  }).join("");
}

const staedte = [...new Set(ANZEIGEN.map(a => a.stadt).filter(Boolean))].sort();
if (staedte.length > 1){
  el("stadtfeld").hidden = false;
  el("stadt").innerHTML = '<option value="">alle</option>' +
    staedte.map(s => `<option value="${s}">${s}</option>`).join("");
  el("stadt").addEventListener("change", zeichneListe);
}

document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    chip.setAttribute("aria-pressed", chip.getAttribute("aria-pressed") === "true" ? "false" : "true");
    zeichneListe();
  });
});
["maxpreis","minzimmer","minflaeche","suchtext"].forEach(id =>
  el(id).addEventListener("input", zeichneListe));

zeichneListe();
</script>
</body>
</html>
"""


def _quellen_block(berichte: list[dict]) -> str:
    zeilen = []
    for bericht in berichte:
        ok = bericht["fehler"] is None
        status = "OK" if ok else "FEHLER"
        klasse = "ok" if ok else "fehler"
        detail = (f"{bericht['treffer']} Anzeigen gelesen" if ok else bericht["fehler"])
        zeilen.append(
            f'<div class="quelle"><span class="status {klasse}">{status}</span>'
            f'<div><div>{bericht["name"]}</div>'
            f'<div class="hinweis">{detail}</div></div></div>'
        )
    return "".join(zeilen) or '<div class="quelle">Noch keine Quellen konfiguriert.</div>'


def dashboard_schreiben(pfad, anzeigen: list[dict], berichte: list[dict], takt: int) -> None:
    fehler = [b for b in berichte if b["fehler"]]
    stand = datetime.now(timezone.utc).astimezone().strftime("%d.%m. %H:%M")

    html = (
        TEMPLATE
        .replace("__DATEN__", json.dumps(anzeigen, ensure_ascii=False))
        .replace("__STAND__", stand)
        .replace("__QUELLEN__", _quellen_block(berichte))
        .replace("__QUELLEN_ZAHL__", str(len(berichte)))
        .replace("__FEHLER_ZAHL__", str(len(fehler)))
        .replace("__QUELLEN_OFFEN__", "open" if fehler else "")
        .replace("__TAKT__", str(takt))
    )
    pfad.write_text(html, encoding="utf-8")
