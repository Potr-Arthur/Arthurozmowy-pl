#!/usr/bin/env python3
"""Sprawdza treści arthurozmowy.pl przed publikacją.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/sprawdz_tresci.py
Błędy (BŁĄD) zatrzymują publikację, uwagi (UWAGA) są do decyzji, a lista ZAŚLEPKI pokazuje,
czego brakuje, zanim strona wyjdzie. Kod wyjścia 1 oznacza co najmniej jeden błąd.
"""
from pathlib import Path
import re, sys
import yaml

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "src" / "content"
cfg = yaml.safe_load((ROOT / "public/admin/config.yml").read_text(encoding="utf-8"))
ust = yaml.safe_load((C / "ustawienia/witryna.yml").read_text(encoding="utf-8"))
baza = yaml.safe_load((C / "pytania/baza.yml").read_text(encoding="utf-8"))["pytania"]
strony = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted((C / "strony").glob("*.yml"))}

bledy, uwagi, zaslepki = [], [], []
def blad(m): bledy.append(m)
def uwaga(m): uwagi.append(m)

# ------------------------------------------------ 1. każde pole treści ma pole w CMS

def pola_cfg(kolekcja, plik):
    for col in cfg["collections"]:
        if col["name"] == kolekcja:
            for f in col["files"]:
                if f["name"] == plik:
                    return f["fields"]
    raise KeyError(plik)

def sprawdz_pokrycie(dane, pola, sciezka):
    if not isinstance(dane, dict):
        return
    mapa = {p["name"]: p for p in pola}
    for k, v in dane.items():
        p = mapa.get(k)
        if p is None:
            blad(f"{sciezka}.{k}: pole w treści nie ma pola w CMS")
            continue
        w = p.get("widget")
        if w == "object":
            sprawdz_pokrycie(v, p["fields"], f"{sciezka}.{k}")
        elif w == "list" and isinstance(v, list):
            for i, el in enumerate(v):
                if "types" in p:
                    typ = el.get(p.get("typeKey", "type"))
                    t = next((x for x in p["types"] if x["name"] == typ), None)
                    if t is None:
                        blad(f"{sciezka}.{k}[{i}]: nieznany typ sekcji {typ!r}")
                        continue
                    sprawdz_pokrycie({a: b for a, b in el.items() if a != p.get("typeKey")}, t["fields"],
                                     f"{sciezka}.{k}[{i}:{typ}]")
                elif "fields" in p:
                    sprawdz_pokrycie(el, p["fields"], f"{sciezka}.{k}[{i}]")

for nazwa, d in strony.items():
    sprawdz_pokrycie(d, pola_cfg("strony", nazwa), nazwa)
sprawdz_pokrycie({"pytania": baza}, pola_cfg("pytania", "baza"), "baza")
sprawdz_pokrycie(ust, pola_cfg("ustawienia", "witryna"), "ustawienia")
cfg_pliki = {f["name"] for col in cfg["collections"] if col["name"] == "strony" for f in col["files"]}
if cfg_pliki != set(strony):
    blad(f"Pliki stron i wpisy w CMS się różnią: {sorted(cfg_pliki ^ set(strony))}")

# ------------------------------------------------ 2. zbieranie tekstów

FIRMA = (f"{ust['firma']['nazwa']}, {ust['firma']['ulica']}, {ust['firma']['kod_pocztowy']} "
         f"{ust['firma']['miejscowosc']}, NIP {ust['firma']['nip']}")

UKRYTE = set()  # ścieżki obiektów z widoczne/widoczny = false

def teksty(o, sciezka=""):
    """Zwraca pary (ścieżka, tekst) dla wszystkich napisów w obiekcie."""
    if isinstance(o, str):
        yield sciezka, o
    elif isinstance(o, dict):
        if o.get("widoczne") is False or o.get("widoczny") is False:
            UKRYTE.add(sciezka)
        for k, v in o.items():
            yield from teksty(v, f"{sciezka}.{k}" if sciezka else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from teksty(v, f"{sciezka}[{i}]")

POMIN = re.compile(r"(plik|plik_telefon|adres|kotwica|kadr|warunek|typ|szablon|schemat|ton|wariant)(\[\d+\])?$")

def widoczne_teksty(nazwa, d):
    for sc, tx in teksty(d):
        if POMIN.search(sc) or sc.startswith("strona."):
            continue
        yield sc, tx

# ------------------------------------------------ 3. słowa zakazane, pisownia, zaślepki

ZAKAZANE = [r"senior\w*", r"podopieczn\w*", r"złot\w+ jesie\w*", r"srebrn\w+ gospodar\w*",
            r"aktywizac\w*", r"monitoring\w*", r"monitoruj\w*", r"kontrol\w*", r"opiekun\w*", r"nowoczesn\w*"]
ZAK_RE = re.compile(r"\b(" + "|".join(ZAKAZANE) + r")\b", re.IGNORECASE)
ZASLEPKA_RE = re.compile(r"\[(?!\s*\])[^\]]+\](?!\()")

def skanuj(nazwa, sc, tx):
    for m in ZAK_RE.finditer(tx):
        slowo = m.group(0)
        przed, po = tx[max(0, m.start() - 1):m.start()], tx[m.end():m.end() + 1]
        if nazwa == "o-nas" and slowo.lower().startswith("senior") and przed == "„" and po == "”":
            continue  # R141: „senior” w cudzysłowie jako cudze słowo
        blad(f"{nazwa} · {sc}: słowo zakazane „{slowo}”")
    if re.search(r"\bArtur\b", tx):
        blad(f"{nazwa} · {sc}: „Artur” bez „h”")
    for m in re.finditer(r"Arthurozm\w*", tx):
        przed = tx[:m.start()].rstrip()
        if przed and przed[-1] not in ".!?:„\"(" and not sc.endswith("tytul"):
            uwaga(f"{nazwa} · {sc}: „{m.group(0)}” wielką literą w środku zdania")
    if any(sc.startswith(u + ".") for u in UKRYTE if u):
        return  # zaślepka w ukrytym elemencie nie blokuje strony
    for m in ZASLEPKA_RE.finditer(tx):
        zaslepki.append(f"{nazwa} · {sc}: {m.group(0)}")

for nazwa, d in strony.items():
    for sc, tx in widoczne_teksty(nazwa, d):
        skanuj(nazwa, sc, tx)
for i, q in enumerate(baza):
    for sc, tx in teksty(q):
        if not POMIN.search(sc):
            skanuj("baza", f"{q['id']}.{sc}", tx)
for sc, tx in teksty(ust):
    if not POMIN.search(sc) and not sc.startswith(("firma.email", "firma.panel", "marka.domena")):
        skanuj("ustawienia", sc, tx)

# ------------------------------------------------ 4. SEO, nagłówki, kotwice, linki

adresy = {d["seo"]["adres"]: n for n, d in strony.items()}
kotwice = {n: set() for n in strony}
for n, d in strony.items():
    k = d["wejscie"].get("kotwica")
    if k: kotwice[n].add(k)
    for sek in d.get("sekcje", []):
        if sek.get("kotwica"):
            if sek["kotwica"] in kotwice[n]:
                blad(f"{n}: powtórzona kotwica #{sek['kotwica']}")
            kotwice[n].add(sek["kotwica"])
ZEWNETRZNE_DO_ZBUDOWANIA = {"/regulamin", "/prywatnosc", "/umow"}

def sprawdz_link(zrodlo, adres, aktywny=True):
    if not aktywny or not adres:
        return
    if adres.startswith("http"):
        return
    sciezka, _, kot = adres.partition("#")
    sciezka = sciezka or "/"
    if sciezka in ZEWNETRZNE_DO_ZBUDOWANIA:
        uwaga(f"{zrodlo}: link do {sciezka}, strony jeszcze nie ma")
        return
    cel = adresy.get(sciezka)
    if cel is None:
        blad(f"{zrodlo}: link do nieistniejącej strony {adres}")
    elif kot and kot not in kotwice[cel]:
        blad(f"{zrodlo}: link do nieistniejącej kotwicy {adres}")

MD_LINK = re.compile(r"\]\(([^)]+)\)")
for n, d in strony.items():
    seo = d["seo"]
    if seo["indeksuj"]:
        lt, lo = len(seo["tytul"]), len(seo["opis"])
        if lt > 70: blad(f"{n}: tytuł ma {lt} znaków (maks. 70)")
        elif lt > 60: uwaga(f"{n}: tytuł ma {lt} znaków (zalecane do 60)")
        if not 110 <= lo <= 160: blad(f"{n}: opis ma {lo} znaków (110–160)")
        elif lo > 155: uwaga(f"{n}: opis ma {lo} znaków (zalecane do 155)")
        if not d["geo"]["streszczenie"]:
            blad(f"{n}: brak streszczenia dla AI")
    if not d["wejscie"].get("h1"):
        blad(f"{n}: brak H1")
    if "\n" in d["wejscie"]["h1"]:
        blad(f"{n}: H1 zawiera Enter")
    poprzedni_ton = None
    okna = 0
    for i, sek in enumerate(d.get("sekcje", [])):
        typ = sek["typ"]
        miejsce = f"{n} · sekcja {i + 1} ({sek.get('etykieta') or typ})"
        if typ not in ("pytania", "koniec", "faq") and not sek.get("h2") and sek.get("etykieta"):
            blad(f"{miejsce}: sekcja w spisie treści bez H2")
        if sek.get("h2") and "\n" in sek["h2"]:
            blad(f"{miejsce}: H2 zawiera Enter")
        if sek.get("etykieta") and not sek.get("kotwica"):
            blad(f"{miejsce}: etykieta bez kotwicy")
        if sek.get("ton") == poprzedni_ton:
            uwaga(f"{miejsce}: ten sam ton co sekcja wyżej ({poprzedni_ton})")
        poprzedni_ton = sek.get("ton")
        for l in sek.get("linki", []) or []:
            sprawdz_link(miejsce, l.get("adres"), l.get("aktywny", True))
        for pole in ("tekst", "tekst_po"):
            for a in MD_LINK.findall(sek.get(pole) or ""):
                sprawdz_link(miejsce, a)
        og = sek.get("okno_glosu")
        if og and og.get("widoczne"):
            okna += 1
            if og.get("dialog") and (og.get("etykieta") != "Przykład rozmowy" or not og.get("przypis")):
                blad(f"{miejsce}: przykład rozmowy bez etykiety „Przykład rozmowy” albo bez przypisu")
            if (og.get("nagranie") or {}).get("plik") and not og["nagranie"].get("transkrypcja"):
                blad(f"{miejsce}: nagranie bez transkrypcji")
        cz = sek.get("cudze_zdanie")
        if cz and cz.get("widoczne") and not cz.get("zgoda"):
            blad(f"{miejsce}: cudze zdanie bez udokumentowanej zgody")
        if typ in ("pytania", "faq"):
            for pid in sek.get("pytania", []):
                if pid not in {q["id"] for q in baza}:
                    blad(f"{miejsce}: pytania {pid!r} nie ma w bazie")
            if typ == "faq" and len(sek.get("pytania", [])) != 3:
                blad(f"{miejsce}: akordeon ma {len(sek.get('pytania', []))} pytań zamiast 3")
        z = sek.get("zdjecie")
        if z and z.get("widoczne"):
            if not z.get("alt") or z["alt"].startswith("["):
                blad(f"{miejsce}: widoczne zdjęcie bez tekstu alternatywnego")
        elif z and not z.get("widoczne"):
            uwaga(f"{miejsce}: miejsce na zdjęcie ukryte, czeka na wybór kadru ({z.get('kadr', '')})")
    if okna > 3:
        blad(f"{n}: {okna} okna głosu (maks. 3 na stronę)")
    w = d["wejscie"]
    for a in MD_LINK.findall(w.get("lid") or ""):
        sprawdz_link(f"{n} · wstęp", a)
    for l in w.get("linki", []) or []:
        sprawdz_link(f"{n} · wejście", l.get("adres"), l.get("aktywny", True))
    zw = w.get("zdjecie") or {}
    if zw.get("widoczne") and (not zw.get("alt") or zw["alt"].startswith("[")):
        blad(f"{n}: zdjęcie wejścia bez tekstu alternatywnego")
    elif not zw.get("widoczne") and d["strona"]["szablon"] != "blad":
        uwaga(f"{n}: zdjęcie wejścia ukryte, czeka na wybór kadru")

for q in baza:
    if q.get("link"):
        sprawdz_link(f"baza · {q['id']}", q["link"].get("adres"))
for l in ust["nawigacja"]["strony"]:
    sprawdz_link("nawigacja", l["adres"])
for l in ust["stopka"]["linki_prawne"]:
    sprawdz_link("stopka", l["adres"])

# ------------------------------------------------ 4a. teksty alternatywne zdjęć

ALT_ZAKAZ = re.compile(r"\b(Arthur\w*|arthurozm\w*|AI|SI|sztuczn\w+ inteligenc\w+)\b", re.IGNORECASE)
for n, d in strony.items():
    for sc, tx in teksty(d):
        if not sc.endswith(".alt") or not tx:
            continue
        if ALT_ZAKAZ.search(tx):
            blad(f"{n} · {sc}: alt zdjęcia człowieka zawiera „{ALT_ZAKAZ.search(tx).group(0)}” (Arthur nie ma twarzy)")
        if not tx.startswith("[") and not 50 <= len(tx) <= 125:
            uwaga(f"{n} · {sc}: alt ma {len(tx)} znaków (zalecane 50–125)")

# ------------------------------------------------ 5. baza pytań

ids = [q["id"] for q in baza]
if len(ids) != len(set(ids)):
    blad("baza: powtórzone identyfikatory pytań")
na_pytaniach = [pid for s in strony["pytania"]["sekcje"] if s["typ"] == "pytania" for pid in s["pytania"]]
if sorted(na_pytaniach) != sorted(ids):
    blad(f"Pytania: strona i baza się różnią: {sorted(set(ids) ^ set(na_pytaniach))}")
for q in baza:
    if not q["pytanie"].endswith("?"):
        uwaga(f"baza · {q['id']}: pytanie bez znaku zapytania")

# ------------------------------------------------ 6. spójność definicji i cen

definicja = ust["marka"]["definicja"].strip()
odp = next(q for q in baza if q["id"] == "czym-sa-arthurozmowy")["odpowiedz"]
if not odp.startswith(definicja):
    blad("Definicja w Ustawieniach różni się od odpowiedzi „Czym są arthurozmowy?” (R167)")
for p in ust["pakiety"]["lista"]:
    if str(p["rozmowy_pelne"]) not in p["opis"] or str(p["rozmowy_podtrzymujace"]) not in p["opis"]:
        blad(f"Pakiet {p['cena']} zł: liczby w opisie nie zgadzają się z polami")

# ------------------------------------------------ 7. jeden temat, jedna nazwa (decyzja z 4.11.2026)

nazwy_stron = {l["tekst"]: l["adres"] for l in ust["nawigacja"]["strony"]}
adres_strony = {d["seo"]["adres"]: n for n, d in strony.items()}
for l in ust["nawigacja"]["strony"]:
    cel = adres_strony.get(l["adres"])
    if cel and strony[cel]["strona"]["nazwa"] != l["tekst"]:
        blad(f"nawigacja: „{l['tekst']}” różni się od nazwy strony „{strony[cel]['strona']['nazwa']}”")
etykiety = {}
for n, d in strony.items():
    rozdzialy = ([d["wejscie"]] if d["wejscie"].get("etykieta") else []) + [s for s in d.get("sekcje") or [] if s.get("etykieta")]
    for s in rozdzialy:
        e = s["etykieta"]
        etykiety.setdefault(e, []).append(n)
        if e in nazwy_stron:
            if n != "strona-glowna":
                blad(f"{n}: rozdział „{e}” nazywa się jak strona {nazwy_stron[e]}")
            elif nazwy_stron[e] not in [(l.get("adres") or "").split("#")[0] for l in s.get("linki") or []]:
                blad(f"strona główna: rozdział „{e}” nie prowadzi do strony {nazwy_stron[e]}")
        for l in s.get("linki") or []:
            sciezka = (l.get("adres") or "").split("#")[0]
            nazwa = next((k for k, v in nazwy_stron.items() if v == sciezka), None)
            if nazwa and "#" not in (l.get("adres") or "") and l["tekst"] != nazwa:
                blad(f"{n}: link „{l['tekst']}” do {sciezka} ma inną nazwę niż strona („{nazwa}”)")
for e, gdzie in etykiety.items():
    if len(gdzie) > 1:
        uwaga(f"Rozdział „{e}” jest na stronach: {', '.join(gdzie)} (dozwolone tylko dla tego samego tematu)")

# ------------------------------------------------ 8. liczba zdjęć (zasada z 5.11.2026)

pliki_zdjec = {}
for n, d in strony.items():
    zz = [d["wejscie"].get("zdjecie") or {}] + [s.get("zdjecie") or {} for s in d.get("sekcje") or []]
    zz = [z for z in zz if z.get("plik")]
    oczekiwane = 4 if d["strona"]["szablon"] == "glowna" else (0 if d["strona"]["szablon"] == "blad" else 2)
    if len(zz) != oczekiwane:
        blad(f"{n}: {len(zz)} zdjęć, a powinno być {oczekiwane} (główna 4, podstrona 2, 404 zero)")
    if oczekiwane and not (d["wejscie"].get("zdjecie") or {}).get("plik"):
        blad(f"{n}: brak zdjęcia wejścia")
    for z in zz:
        plik = z["plik"].rsplit("/", 1)[-1]
        if plik in pliki_zdjec:
            blad(f"{n}: plik {plik} jest też na stronie {pliki_zdjec[plik]} (każde miejsce ma własny plik)")
        pliki_zdjec[plik] = n
        for pole in ("plik", "plik_telefon"):
            if pole == "plik_telefon" and not z.get(pole):
                continue
            if not (ROOT / "public" / (z.get(pole) or "").lstrip("/")).is_file():
                (blad if z.get("widoczne") else uwaga)(f"{n}: brak pliku {z.get(pole) or '(puste pole ' + pole + ')'} w public/")
    og = (d.get("seo") or {}).get("obraz_og") or {}
    if og.get("plik") and not (ROOT / "public" / og["plik"].lstrip("/")).is_file():
        uwaga(f"{n}: brak obrazu do udostępniania {og['plik']} w public/")

# ------------------------------------------------ raport

def wypisz(tytul, lista):
    print(f"\n{tytul} ({len(lista)})")
    for x in lista:
        print("  -", x)

wypisz("BŁĘDY", bledy)
wypisz("UWAGI", uwagi)
wypisz("ZAŚLEPKI (strona z zaślepką nie wychodzi)", zaslepki)
print(f"\nStrony: {len(strony)}, pytania w bazie: {len(baza)}.")
sys.exit(1 if bledy else 0)
