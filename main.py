"""Wohnungsradar - sucht konfigurierte Plattformen ab und baut das Dashboard.

Aufruf:  python main.py            normaler Lauf
         python main.py --debug    speichert das rohe HTML nach data/debug/
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from render import dashboard_schreiben
from sources import BROWSER_HEADERS, suche_abrufen

WURZEL = Path(__file__).parent
CONFIG = WURZEL / "config.json"
SPEICHER = WURZEL / "data" / "anzeigen.json"
DASHBOARD = WURZEL / "docs" / "index.html"
DEBUG = "--debug" in sys.argv


def config_laden() -> dict:
    if not CONFIG.exists():
        sys.exit("config.json fehlt.")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def gespeicherte_laden() -> dict[str, dict]:
    if not SPEICHER.exists():
        return {}
    try:
        return {a["id"]: a for a in json.loads(SPEICHER.read_text(encoding="utf-8"))}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def passt_zu_filtern(anzeige: dict, filter_regeln: dict) -> bool:
    """Ein fehlender Wert schliesst nicht aus - viele Anzeigen sind unvollstaendig,
    und eine passende Wohnung wegen einer fehlenden Zahl zu verwerfen waere teurer
    als ein Fehltreffer in der Liste."""
    max_miete = filter_regeln.get("max_miete")
    if max_miete and anzeige.get("preis") and anzeige["preis"] > max_miete:
        return False
    min_zimmer = filter_regeln.get("min_zimmer")
    if min_zimmer and anzeige.get("zimmer") and anzeige["zimmer"] < min_zimmer:
        return False
    min_flaeche = filter_regeln.get("min_flaeche")
    if min_flaeche and anzeige.get("flaeche") and anzeige["flaeche"] < min_flaeche:
        return False

    text = f"{anzeige.get('titel','')} {anzeige.get('ort','')}".lower()
    for wort in filter_regeln.get("ausschluss_woerter", []):
        if wort.lower() in text:
            return False
    pflicht = filter_regeln.get("pflicht_woerter", [])
    if pflicht and not any(w.lower() in text for w in pflicht):
        return False
    return True


def main() -> None:
    config = config_laden()
    filter_regeln = config.get("filter", {})
    behalten_tage = int(config.get("behalten_tage", 14))
    takt = int(config.get("takt_minuten", 20))

    bestand = gespeicherte_laden()
    berichte: list[dict] = []
    neu_gesamt = 0

    for suche in config.get("suchen", []):
        if suche.get("aktiv") is False:
            continue
        name = suche.get("name", suche["url"])
        # Eigene Filter einer Suche ueberschreiben die globalen, Rest bleibt gueltig
        regeln = {**filter_regeln, **suche.get("filter", {})}
        treffer, fehler = suche_abrufen(suche)

        if DEBUG and fehler:
            ordner = WURZEL / "data" / "debug"
            ordner.mkdir(parents=True, exist_ok=True)
            try:
                roh = requests.get(suche["url"], headers=BROWSER_HEADERS, timeout=25).text
                datei = ordner / (name.replace("/", "_")[:60] + ".html")
                datei.write_text(roh, encoding="utf-8")
                print(f"   HTML gespeichert: {datei}")
            except requests.RequestException:
                pass

        passend = 0
        for eintrag in treffer:
            daten = eintrag.as_dict()
            if not passt_zu_filtern(daten, regeln):
                continue
            passend += 1
            if daten["id"] not in bestand:
                bestand[daten["id"]] = daten
                neu_gesamt += 1
            else:
                # Bekannte Anzeige: Angaben auffrischen, damit Korrekturen am Parser
                # auch alte Eintraege erreichen. Der Fundzeitpunkt bleibt unangetastet.
                alt = bestand[daten["id"]]
                for feld in ("titel", "preis", "zimmer", "flaeche", "ort", "stadt"):
                    neu = daten.get(feld)
                    if neu and neu != "Ohne Titel":
                        alt[feld] = neu

        berichte.append({"name": name, "fehler": fehler, "treffer": passend})
        print(f"{'✗' if fehler else '✓'} {name}: "
              f"{fehler or f'{len(treffer)} gelesen, {passend} nach Filter'}")

        time.sleep(random.uniform(2.5, 6.0))  # freundlicher Abstand zwischen Abrufen

    grenze = datetime.now(timezone.utc) - timedelta(days=behalten_tage)
    aktuell = [
        a for a in bestand.values()
        if datetime.fromisoformat(a["gefunden_am"]) > grenze
    ]
    aktuell.sort(key=lambda a: a["gefunden_am"], reverse=True)

    SPEICHER.parent.mkdir(parents=True, exist_ok=True)
    SPEICHER.write_text(json.dumps(aktuell, ensure_ascii=False, indent=1), encoding="utf-8")
    DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    dashboard_schreiben(DASHBOARD, aktuell, berichte, takt)

    print(f"\n{neu_gesamt} neue Anzeigen · {len(aktuell)} insgesamt im Dashboard")


if __name__ == "__main__":
    main()
