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

POMIN = re.compile(r"(plik|plik_telefon|adres|kotwica|typ|rodzaj|szablon|schemat|ton|id)(\[\d+\])?$")

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

# ------------------------------------------------ 4. SEO, nagłówki, kotwice, linki, bloki

adresy = {d["seo"]["adres"]: n for n, d in strony.items()}
nazwy_stron = {l["tekst"]: l["adres"] for l in ust["nawigacja"]["strony"]}
nazwa_po_adresie = {v: k for k, v in nazwy_stron.items()}
kotwice = {n: {} for n in strony}   # kotwica → nazwa rozdziału w spisie treści (albo None)
for n, d in strony.items():
    k = d["wejscie"].get("kotwica")
    if k: kotwice[n][k] = d["wejscie"].get("etykieta")
    for sek in d.get("sekcje", []):
        if sek.get("kotwica"):
            if sek["kotwica"] in kotwice[n]:
                blad(f"{n}: powtórzona kotwica #{sek['kotwica']}")
            kotwice[n][sek["kotwica"]] = sek.get("etykieta")
DO_ZBUDOWANIA = {"/regulamin-strony", "/regulamin-uslugi", "/prywatnosc", "/umow"}
WSZYSTKIE_PYTANIA = ust["nawigacja"]["wszystkie_pytania"]

def sprawdz_link(zrodlo, adres, tekst=None, aktywny=True):
    """Link istnieje, a jego tekst to nazwa strony albo rozdziału, do którego prowadzi (jeden temat, jedna nazwa)."""
    if not aktywny or not adres or adres.startswith("http"):
        return
    sciezka, _, kot = adres.partition("#")
    sciezka = sciezka or "/"
    if sciezka in DO_ZBUDOWANIA:
        uwaga(f"{zrodlo}: link do {sciezka}, strony jeszcze nie ma")
        return
    cel = adresy.get(sciezka)
    if cel is None:
        blad(f"{zrodlo}: link do nieistniejącej strony {adres}")
        return
    if kot and kot not in kotwice[cel]:
        blad(f"{zrodlo}: link do nieistniejącej kotwicy {adres}")
        return
    if tekst is None:
        return
    if kot:
        oczekiwany = kotwice[cel][kot]
        if oczekiwany and tekst != oczekiwany:
            uwaga(f"{zrodlo}: link „{tekst}” do {adres} ma inną nazwę niż rozdział („{oczekiwany}”)")
    else:
        oczekiwany = strony[cel]["strona"]["nazwa"]
        if tekst != oczekiwany:
            blad(f"{zrodlo}: link „{tekst}” do {sciezka} ma inną nazwę niż strona („{oczekiwany}”)")

MD_LINK = re.compile(r"\]\(([^)]+)\)")
ZNACZNIK = re.compile(r"\{(\w+)\}")
ZNACZNIKI = {"firma", "email", "telefon", "godziny"}
ID_BAZY = {q["id"] for q in baza}

def sprawdz_tekst(miejsce, tx):
    for a in MD_LINK.findall(tx or ""):
        sprawdz_link(miejsce, a)
    for z in ZNACZNIK.findall(tx or ""):
        if z not in ZNACZNIKI:
            blad(f"{miejsce}: nieznany znacznik {{{z}}} (dozwolone: {', '.join(sorted(ZNACZNIKI))})")

def sprawdz_bloki(miejsce, bloki):
    for j, bl in enumerate(bloki or []):
        typ, gdzie = bl.get("typ"), f"{miejsce} · blok {j + 1} ({bl.get('typ')})"
        if typ in ("tekst", "glos"):
            if not (bl.get("tekst") or "").strip():
                blad(f"{gdzie}: pusty tekst")
            sprawdz_tekst(gdzie, bl.get("tekst"))
        elif typ == "lista":
            if not bl.get("punkty"):
                blad(f"{gdzie}: lista bez punktów")
        elif typ == "zasady":
            for z in bl.get("zasady") or []:
                if not z.get("naglowek"):
                    blad(f"{gdzie}: zasada bez nagłówka")
        elif typ == "cytat":
            if bl.get("widoczny", True):
                if not bl.get("repliki") and not bl.get("wstep"):
                    blad(f"{gdzie}: widoczna karta cytatu bez treści")
                if any((r.get("kto") or "") == "Arthur" for r in bl.get("repliki") or []) and bl.get("etykieta") != "Przykład rozmowy":
                    blad(f"{gdzie}: przykładowy dialog z Arthurem bez etykiety „Przykład rozmowy”")
            else:
                uwaga(f"{gdzie}: karta cytatu ukryta („{bl.get('etykieta') or ''}”)")
        elif typ == "link":
            sprawdz_link(gdzie, bl.get("adres"), bl.get("tekst"), bl.get("aktywny", True))
        elif typ == "wezwanie":
            if bl.get("rodzaj") not in ust["wezwania"]:
                blad(f"{gdzie}: nieznany przycisk {bl.get('rodzaj')!r}")
            if bl.get("objasnienie") and bl.get("rodzaj") != "glowne":
                blad(f"{gdzie}: objaśnienie pod przyciskiem ma tylko „{ust['wezwania']['glowne']['przycisk']}”")
        elif typ in ("pytania", "faq"):
            for pid in bl.get("pytania") or []:
                if pid not in ID_BAZY:
                    blad(f"{gdzie}: pytania {pid!r} nie ma w bazie")
            if typ == "faq" and len(bl.get("pytania") or []) != 3:
                blad(f"{gdzie}: akordeon ma {len(bl.get('pytania') or [])} pytań zamiast 3")
        elif typ != "cennik":
            blad(f"{gdzie}: nieznany typ bloku")

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
    w = d["wejscie"]
    if not w.get("h1"):
        blad(f"{n}: brak H1")
    if "\n" in (w.get("h1") or ""):
        blad(f"{n}: H1 zawiera Enter")
    if w.get("etykieta") and not w.get("kotwica"):
        blad(f"{n} · wejście: nazwa w spisie treści bez kotwicy")
    sprawdz_tekst(f"{n} · wejście", w.get("lid"))
    sprawdz_bloki(f"{n} · wejście", w.get("bloki"))
    zw = w.get("zdjecie") or {}
    if zw.get("widoczne") and (not zw.get("alt") or zw["alt"].startswith("[")):
        blad(f"{n}: zdjęcie wejścia bez tekstu alternatywnego")
    poprzedni_ton = None
    for i, sek in enumerate(d.get("sekcje", [])):
        miejsce = f"{n} · rozdział {i + 1} ({sek.get('etykieta') or sek.get('kotwica') or 'bez nazwy'})"
        if not sek.get("h2"):
            blad(f"{miejsce}: rozdział bez H2")
        elif "\n" in sek["h2"]:
            blad(f"{miejsce}: H2 zawiera Enter")
        if sek.get("etykieta") and not sek.get("kotwica"):
            blad(f"{miejsce}: nazwa w spisie treści bez kotwicy")
        if sek.get("ton") == poprzedni_ton:
            uwaga(f"{miejsce}: ten sam ton co rozdział wyżej ({poprzedni_ton})")
        poprzedni_ton = sek.get("ton")
        if not sek.get("bloki") and not sek.get("lid"):
            blad(f"{miejsce}: rozdział bez lidu i bez bloków")
        sprawdz_tekst(miejsce, sek.get("lid"))
        sprawdz_bloki(miejsce, sek.get("bloki"))
        z = sek.get("zdjecie")
        if z and z.get("widoczne"):
            if not z.get("alt") or z["alt"].startswith("["):
                blad(f"{miejsce}: widoczne zdjęcie bez tekstu alternatywnego")
        elif z and z.get("plik"):
            uwaga(f"{miejsce}: zdjęcie ukryte ({z['plik'].rsplit('/', 1)[-1]})")

for q in baza:
    if q.get("link"):
        sprawdz_link(f"baza · {q['id']}", q["link"].get("adres"), q["link"].get("tekst"))
for l in ust["nawigacja"]["strony"]:
    sprawdz_link("nawigacja", l["adres"], l["tekst"])
for l in ust["naglowek"]["linki"]:
    sprawdz_link("belka górna", l["adres"], l["tekst"])
for l in ust["stopka"]["linki_prawne"]:
    sprawdz_link("stopka", l["adres"])
for r in ust["stopka"]["wezwania"]:
    if r not in ust["wezwania"]:
        blad(f"stopka: nieznany przycisk {r!r}")
if set(adresy) - {"/404"} != set(nazwy_stron.values()):
    blad(f"Lista stron w nawigacji i pliki stron się różnią: {sorted((set(adresy) - {'/404'}) ^ set(nazwy_stron.values()))}")

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
na_pytaniach = [pid for s in strony["pytania"]["sekcje"] for bl in s.get("bloki") or [] if bl["typ"] == "pytania" for pid in bl["pytania"]]
if sorted(na_pytaniach) != sorted(ids):
    blad(f"Pytania: strona i baza się różnią: {sorted(set(ids) ^ set(na_pytaniach))}")
for q in baza:
    if not q["pytanie"].endswith("?"):
        uwaga(f"baza · {q['id']}: pytanie bez znaku zapytania")
for n, d in strony.items():
    if n != "pytania" and any(bl["typ"] == "pytania" for s in d.get("sekcje") or [] for bl in s.get("bloki") or []):
        blad(f"{n}: karty pytań (blok „pytania”) stoją tylko na stronie Pytania; na podstronach użyj akordeonu „faq”")

# ------------------------------------------------ 6. spójność definicji i cen

definicja = ust["marka"]["definicja"].strip()
odp = next(q for q in baza if q["id"] == "czym-sa-arthurozmowy")["odpowiedz"]
if not odp.startswith(definicja):
    blad("Definicja w Ustawieniach różni się od odpowiedzi „Czym są arthurozmowy?”")
for p in ust["pakiety"]["lista"]:
    if str(p["rozmowy_pelne"]) not in p["opis"] or str(p["rozmowy_podtrzymujace"]) not in p["opis"]:
        blad(f"Pakiet {p['cena']} zł: liczby w opisie nie zgadzają się z polami")

# ------------------------------------------------ 7. jeden temat, jedna nazwa

for l in ust["nawigacja"]["strony"]:
    cel = adresy.get(l["adres"])
    if cel and strony[cel]["strona"]["nazwa"] != l["tekst"]:
        blad(f"nawigacja: „{l['tekst']}” różni się od nazwy strony „{strony[cel]['strona']['nazwa']}”")
etykiety = {}
for n, d in strony.items():
    rozdzialy = ([d["wejscie"]] if d["wejscie"].get("etykieta") else []) + [s for s in d.get("sekcje") or [] if s.get("etykieta")]
    for s in rozdzialy:
        e = s["etykieta"]
        etykiety.setdefault(e, []).append(n)
        if e in nazwy_stron and nazwy_stron[e] != d["seo"]["adres"]:
            cele = [(bl.get("adres") or "").split("#")[0] for bl in s.get("bloki") or [] if bl["typ"] == "link"]
            if n != "strona-glowna":
                blad(f"{n}: rozdział „{e}” nazywa się jak strona {nazwy_stron[e]}")
            elif nazwy_stron[e] not in cele:
                blad(f"strona główna: rozdział „{e}” nie prowadzi do strony {nazwy_stron[e]}")
for e, gdzie in etykiety.items():
    if len(gdzie) > 1:
        uwaga(f"Rozdział „{e}” jest na stronach: {', '.join(gdzie)} (dozwolone tylko dla tego samego tematu)")

# ------------------------------------------------ 8. zdjęcia: liczba, pliki, format

def wymiary_webp(sciezka):
    """Szerokość i wysokość pliku WebP odczytane z nagłówka (bez dodatkowych bibliotek)."""
    try:
        h = sciezka.read_bytes()[:32]
    except OSError:
        return None
    if h[:4] != b"RIFF" or h[8:12] != b"WEBP":
        return None
    rodzaj = h[12:16]
    if rodzaj == b"VP8X":
        return 1 + int.from_bytes(h[24:27], "little"), 1 + int.from_bytes(h[27:30], "little")
    if rodzaj == b"VP8 ":
        return int.from_bytes(h[26:28], "little") & 0x3FFF, int.from_bytes(h[28:30], "little") & 0x3FFF
    if rodzaj == b"VP8L":
        bity = int.from_bytes(h[21:25], "little")
        return (bity & 0x3FFF) + 1, ((bity >> 14) & 0x3FFF) + 1
    return None

FORMATY = {"21x9": 21 / 9, "4x3": 4 / 3, "1x1": 1.0}

def sprawdz_plik(n, sciezka, format_, widoczne):
    zglos = blad if widoczne else uwaga
    if not sciezka.endswith(f"-{format_}.webp"):
        zglos(f"{n}: plik {sciezka.rsplit('/', 1)[-1]} powinien kończyć się na -{format_}.webp")
    plik = ROOT / "public" / sciezka.lstrip("/")
    if not plik.is_file():
        zglos(f"{n}: brak pliku {sciezka} w public/")
        return
    wym = wymiary_webp(plik)
    if wym and abs(wym[0] / wym[1] - FORMATY[format_]) > 0.02:
        zglos(f"{n}: plik {plik.name} ma {wym[0]} × {wym[1]} px, a powinien mieć proporcje {format_.replace('x', ':')}")

pliki_zdjec = {}
for n, d in strony.items():
    szablon = d["strona"]["szablon"]
    we = d["wejscie"].get("zdjecie") or {}
    zz = ([("wejscie", we)] if we.get("plik") else []) + [("rozdzial", s["zdjecie"]) for s in d.get("sekcje") or [] if (s.get("zdjecie") or {}).get("plik")]
    oczekiwane = 4 if szablon == "glowna" else (0 if szablon == "blad" else 2)
    if len(zz) != oczekiwane:
        blad(f"{n}: {len(zz)} zdjęć, a powinno być {oczekiwane} (główna 4, podstrona 2, 404 zero)")
    if oczekiwane and not we.get("plik"):
        blad(f"{n}: brak zdjęcia wejścia")
    for miejsce, z in zz:
        nazwa_pliku = z["plik"].rsplit("/", 1)[-1]
        if nazwa_pliku in pliki_zdjec:
            blad(f"{n}: plik {nazwa_pliku} jest też na stronie {pliki_zdjec[nazwa_pliku]} (każde miejsce ma własny plik)")
        pliki_zdjec[nazwa_pliku] = n
        widoczne = bool(z.get("widoczne"))
        if miejsce == "wejscie" and szablon == "glowna":
            sprawdz_plik(n, z["plik"], "21x9", widoczne)
            if z.get("plik_telefon"):
                sprawdz_plik(n, z["plik_telefon"], "4x3", widoczne)
            else:
                blad(f"{n}: wejście strony głównej bez kadru 4:3 na telefon (plik_telefon)")
        else:
            sprawdz_plik(n, z["plik"], "1x1" if miejsce == "wejscie" else "4x3", widoczne)
            if z.get("plik_telefon"):
                uwaga(f"{n}: pole plik_telefon ma tylko wejście strony głównej ({nazwa_pliku})")
    og = (d.get("seo") or {}).get("obraz_og") or {}
    if og.get("plik") and not (ROOT / "public" / og["plik"].lstrip("/")).is_file():
        uwaga(f"{n}: brak obrazu do udostępniania {og['plik']} w public/")
uzywane = set(pliki_zdjec) | {(d["wejscie"].get("zdjecie") or {}).get("plik_telefon", "").rsplit("/", 1)[-1] for d in strony.values()}
for plik in sorted((ROOT / "public/images/strony").glob("*")):
    if plik.name not in uzywane:
        uwaga(f"public/images/strony/{plik.name}: plik nie stoi na żadnej stronie (do usunięcia)")

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
