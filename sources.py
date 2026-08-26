"""Abruf und Auswertung der Suchergebnisseiten der einzelnen Plattformen.

Jede Plattform liefert eine Liste von Listing-Objekten. Wenn eine Seite den
Zugriff blockiert oder ihr HTML geaendert hat, wird das als Fehler
zurueckgegeben und im Dashboard sichtbar gemacht - lieber eine gemeldete
Luecke als eine stille.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.6",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class Listing:
    id: str
    plattform: str
    titel: str
    url: str
    preis: float | None = None
    zimmer: float | None = None
    flaeche: float | None = None
    ort: str = ""
    bild: str | None = None
    gefunden_am: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    quelle: str = ""
    stadt: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def _zahl(text: str | None) -> float | None:
    """Zieht die erste Zahl aus einem String, deutsche Schreibweise."""
    if not text:
        return None
    treffer = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:[.,]\d+)?)", text)
    if not treffer:
        return None
    roh = treffer.group(1)
    if "." in roh and "," in roh:
        roh = roh.replace(".", "").replace(",", ".")
    elif "," in roh:
        roh = roh.replace(",", ".")
    elif roh.count(".") == 1 and len(roh.split(".")[1]) == 3:
        roh = roh.replace(".", "")
    try:
        return float(roh)
    except ValueError:
        return None


def _id(plattform: str, url: str) -> str:
    """Stabile ID pro Anzeige - Pfad ohne Query, damit Tracking-Parameter
    nicht dieselbe Wohnung als neu erscheinen lassen."""
    pfad = urlparse(url).path.rstrip("/")
    return f"{plattform}:" + hashlib.sha1(pfad.encode()).hexdigest()[:14]


def _text(knoten) -> str:
    return re.sub(r"\s+", " ", knoten.get_text(" ", strip=True)) if knoten else ""


def _json_aus_script(soup: BeautifulSoup, script_id: str) -> dict | None:
    tag = soup.find("script", id=script_id)
    if not tag or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except json.JSONDecodeError:
        return None


def _tiefensuche(objekt, treffer_test, ergebnisse=None, tiefe=0):
    """Durchsucht verschachteltes JSON nach passenden Dicts."""
    if ergebnisse is None:
        ergebnisse = []
    if tiefe > 14:
        return ergebnisse
    if isinstance(objekt, dict):
        if treffer_test(objekt):
            ergebnisse.append(objekt)
        for wert in objekt.values():
            _tiefensuche(wert, treffer_test, ergebnisse, tiefe + 1)
    elif isinstance(objekt, list):
        for wert in objekt:
            _tiefensuche(wert, treffer_test, ergebnisse, tiefe + 1)
    return ergebnisse


# --------------------------------------------------------------------------
# Parser pro Plattform
# --------------------------------------------------------------------------

def parse_kleinanzeigen(html: str, basis: str) -> list[Listing]:
    soup = BeautifulSoup(html, "lxml")
    treffer: list[Listing] = []
    for artikel in soup.select("article.aditem, li.ad-listitem article"):
        # Eine Anzeige enthaelt mehrere Links auf dasselbe Inserat: Bild, Titel und
        # die Bildanzahl-Markierung. Gezielt den Titel-Link nehmen, sonst landet
        # als Titel z. B. nur die Zahl "2" aus der Bildanzahl im Dashboard.
        link = artikel.select_one(
            "h2 a[href*='/s-anzeige/'], h3 a[href*='/s-anzeige/'], "
            "a.ellipsis[href*='/s-anzeige/']"
        )
        kandidaten = artikel.select("a[href*='/s-anzeige/']")
        if link is None and kandidaten:
            # Notnagel: der Link mit dem laengsten Text ist praktisch immer der Titel
            link = max(kandidaten, key=lambda a: len(_text(a)))
        if not link:
            continue
        url = urljoin(basis, link.get("href", ""))

        titel = _text(link)
        if len(titel) < 8 or titel.replace(".", "").isdigit():
            # Immer noch die Bildanzahl o. ae. erwischt - der Reihe nach nachbessern
            for ersatz in (
                _text(artikel.select_one("h2")),
                _text(artikel.select_one("h3")),
                max((_text(a) for a in kandidaten), key=len, default=""),
                (artikel.select_one("img") or {}).get("alt", "") if artikel.select_one("img") else "",
            ):
                if ersatz and len(ersatz) >= 8 and not ersatz.replace(".", "").isdigit():
                    titel = ersatz
                    break
        titel = titel or "Ohne Titel"

        preis = _zahl(_text(artikel.select_one("[class*='--price']")))
        ort = _text(artikel.select_one("[class*='--top--left']"))

        zimmer = flaeche = None
        for tag in artikel.select("[class*='simpletag'], .text-module-end span"):
            wert = _text(tag)
            if "zimmer" in wert.lower():
                zimmer = _zahl(wert)
            elif "m²" in wert or "m2" in wert:
                flaeche = _zahl(wert)

        bild_tag = artikel.select_one("img")
        bild = bild_tag.get("src") or bild_tag.get("data-imgsrc") if bild_tag else None

        treffer.append(Listing(
            id=_id("kleinanzeigen", url), plattform="kleinanzeigen", titel=titel,
            url=url, preis=preis, zimmer=zimmer, flaeche=flaeche, ort=ort, bild=bild,
        ))
    return treffer


def parse_wg_gesucht(html: str, basis: str) -> list[Listing]:
    soup = BeautifulSoup(html, "lxml")
    treffer: list[Listing] = []
    for karte in soup.select("div.wgg_card.offer_list_item, div[id^='liste-details-ad-']"):
        link = karte.select_one("h3 a[href], a[href*='.html']")
        if not link:
            continue
        url = urljoin(basis, link.get("href", ""))
        titel = _text(link)
        inhalt = _text(karte)

        preis_tag = karte.select_one("div.col-xs-3 b, .card_price, b")
        preis = _zahl(_text(preis_tag))
        if preis is None:
            m = re.search(r"(\d[\d.]*)\s*€", inhalt)
            preis = _zahl(m.group(1)) if m else None

        m = re.search(r"(\d[\d.,]*)\s*m²", inhalt)
        flaeche = _zahl(m.group(1)) if m else None
        m = re.search(r"(\d+)er\s*WG|(\d+)\s*Zimmer", inhalt, re.I)
        zimmer = _zahl(m.group(0)) if m else None

        ort_tag = karte.select_one("div.col-xs-11 span, .card_city")
        treffer.append(Listing(
            id=_id("wg-gesucht", url), plattform="wg-gesucht", titel=titel, url=url,
            preis=preis, zimmer=zimmer, flaeche=flaeche, ort=_text(ort_tag)[:80],
        ))
    return treffer


def parse_immowelt(html: str, basis: str) -> list[Listing]:
    """Immowelt liefert die Ergebnisse als JSON im __NEXT_DATA__-Block."""
    soup = BeautifulSoup(html, "lxml")
    daten = _json_aus_script(soup, "__NEXT_DATA__")
    treffer: list[Listing] = []

    if daten:
        kandidaten = _tiefensuche(
            daten,
            lambda d: ("id" in d or "onlineId" in d) and (
                "prices" in d or "hardFacts" in d or "primaryPrice" in d
            ),
        )
        for eintrag in kandidaten:
            kennung = str(eintrag.get("onlineId") or eintrag.get("id") or "")
            if not kennung:
                continue
            url = urljoin(basis, f"/expose/{kennung}")
            preis = zimmer = flaeche = None
            fakten = eintrag.get("hardFacts") or {}
            if isinstance(fakten, dict):
                preis = _zahl(str(fakten.get("price", {}).get("value", "")))
                zimmer = _zahl(str(fakten.get("numberOfRooms", "")))
                flaeche = _zahl(str(fakten.get("area", "")))
            if preis is None:
                preis = _zahl(str(eintrag.get("primaryPrice", {}).get("amountMin", "")))
            treffer.append(Listing(
                id=_id("immowelt", url), plattform="immowelt",
                titel=str(eintrag.get("title") or "Immowelt-Angebot"), url=url,
                preis=preis, zimmer=zimmer, flaeche=flaeche,
                ort=str((eintrag.get("place") or {}).get("city", "")),
            ))

    if not treffer:  # Fallback auf die HTML-Kacheln
        for karte in soup.select("a[href*='/expose/']"):
            url = urljoin(basis, karte.get("href", ""))
            inhalt = _text(karte)
            if not inhalt:
                continue
            m_p = re.search(r"(\d[\d.]*)\s*€", inhalt)
            m_f = re.search(r"(\d[\d.,]*)\s*m²", inhalt)
            m_z = re.search(r"(\d[\d,]*)\s*Zi", inhalt)
            treffer.append(Listing(
                id=_id("immowelt", url), plattform="immowelt", titel=inhalt[:110],
                url=url, preis=_zahl(m_p.group(1)) if m_p else None,
                zimmer=_zahl(m_z.group(1)) if m_z else None,
                flaeche=_zahl(m_f.group(1)) if m_f else None,
            ))
    return _ohne_dubletten(treffer)


def parse_immoscout(html: str, basis: str) -> list[Listing]:
    """ImmoScout24 haengt die Ergebnisliste als JSON an die Seite."""
    treffer: list[Listing] = []
    m = re.search(r"resultListModel\"?\s*[:=]\s*(\{.*?\})\s*[,;]\s*\n", html, re.S)
    if not m:
        m = re.search(r"IS24\.resultList\s*=\s*(\{.*?\});", html, re.S)
    if m:
        try:
            daten = json.loads(m.group(1))
            eintraege = _tiefensuche(daten, lambda d: "realEstate" in d)
            for eintrag in eintraege:
                objekt = eintrag["realEstate"]
                kennung = str(eintrag.get("@id") or objekt.get("@id") or "")
                url = urljoin(basis, f"/expose/{kennung}")
                preis = _zahl(str((objekt.get("price") or {}).get("value", "")))
                treffer.append(Listing(
                    id=_id("immoscout24", url), plattform="immoscout24",
                    titel=str(objekt.get("title", "ImmoScout-Angebot")), url=url,
                    preis=preis,
                    zimmer=_zahl(str(objekt.get("numberOfRooms", ""))),
                    flaeche=_zahl(str((objekt.get("livingSpace") or ""))),
                    ort=str(((objekt.get("address") or {}).get("city") or "")),
                ))
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    if not treffer:
        soup = BeautifulSoup(html, "lxml")
        for karte in soup.select("article, li[data-id]"):
            link = karte.select_one("a[href*='/expose/']")
            if not link:
                continue
            url = urljoin(basis, link.get("href", ""))
            inhalt = _text(karte)
            m_p = re.search(r"(\d[\d.]*)\s*€", inhalt)
            m_f = re.search(r"(\d[\d.,]*)\s*m²", inhalt)
            m_z = re.search(r"(\d[\d,]*)\s*Zi", inhalt)
            treffer.append(Listing(
                id=_id("immoscout24", url), plattform="immoscout24",
                titel=_text(link)[:110] or inhalt[:110], url=url,
                preis=_zahl(m_p.group(1)) if m_p else None,
                zimmer=_zahl(m_z.group(1)) if m_z else None,
                flaeche=_zahl(m_f.group(1)) if m_f else None,
            ))
    return _ohne_dubletten(treffer)


def _ohne_dubletten(liste: list[Listing]) -> list[Listing]:
    gesehen, raus = set(), []
    for eintrag in liste:
        if eintrag.id in gesehen:
            continue
        gesehen.add(eintrag.id)
        raus.append(eintrag)
    return raus


PARSER = {
    "kleinanzeigen": parse_kleinanzeigen,
    "wg-gesucht": parse_wg_gesucht,
    "immowelt": parse_immowelt,
    "immoscout24": parse_immoscout,
}


# --------------------------------------------------------------------------
# Abruf
# --------------------------------------------------------------------------

def suche_abrufen(suche: dict, timeout: int = 25) -> tuple[list[Listing], str | None]:
    """Ruft eine konfigurierte Suche ab. Rueckgabe: (Treffer, Fehlertext)."""
    plattform = suche["plattform"].lower().strip()
    parser = PARSER.get(plattform)
    if parser is None:
        return [], f"Unbekannte Plattform '{plattform}'"

    url = suche["url"]
    basis = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    try:
        antwort = requests.get(url, headers=BROWSER_HEADERS, timeout=timeout)
    except requests.RequestException as fehler:
        return [], f"Netzwerkfehler: {type(fehler).__name__}"

    if antwort.status_code in (403, 429):
        return [], f"Zugriff blockiert (HTTP {antwort.status_code}) - Bot-Schutz"
    if antwort.status_code >= 400:
        return [], f"HTTP {antwort.status_code}"
    if "captcha" in antwort.text[:4000].lower():
        return [], "Captcha-Seite statt Ergebnissen"

    try:
        treffer = parser(antwort.text, basis)
    except Exception as fehler:  # noqa: BLE001 - defekte Selektoren nicht verschlucken
        return [], f"Auswertung fehlgeschlagen: {type(fehler).__name__}: {fehler}"

    for eintrag in treffer:
        eintrag.quelle = suche.get("name", url)
        eintrag.stadt = suche.get("stadt", "")
    if not treffer:
        return [], "Seite geladen, aber keine Anzeigen erkannt (Selektoren pruefen)"
    return treffer, None
