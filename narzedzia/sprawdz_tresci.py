#!/usr/bin/env python3
"""Sprawdza treści arthurozmowy.pl przed publikacją.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/sprawdz_tresci.py
Błędy (BŁĄD) zatrzymują publikację, uwagi (UWAGA) są do decyzji, a lista ZAŚLEPKI pokazuje,
czego brakuje, zanim strona wyjdzie. Kod wyjścia 1 oznacza co najmniej jeden błąd.

  --podglad   dodatkowo zapisuje wynik dla podglądu wersji roboczej: stronę public/sprawdzenie.html
              i podsumowanie .sprawdzenie.json (plakietka na stronach podglądu); kończy się kodem 0 także
              przy błędach, żeby redaktor zobaczył je w podglądzie. Budowanie produkcyjne biegnie bez tej opcji,
              więc wersja z błędem nie trafi na witrynę.
"""
from pathlib import Path
import html, json, re, sys
import yaml

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "src" / "content"
cfg = yaml.safe_load((ROOT / "public/admin/config.yml").read_text(encoding="utf-8"))
ust = yaml.safe_load((C / "ustawienia/witryna.yml").read_text(encoding="utf-8"))
baza = yaml.safe_load((C / "pytania/baza.yml").read_text(encoding="utf-8"))["pytania"]
def uzupelnij(d):
    """Sveltia zapisuje puste pole jako null (np. zdjęcie rozdziału bez zdjęcia) albo pusty tekst.
    Tu sprowadzamy pola strony, z których korzystają narzędzia, do pustych wartości."""
    seo = d.get("seo") or {}
    seo["opis"] = seo.get("opis") or ""
    og = seo.get("obraz_og") or {}
    seo["obraz_og"] = {"plik": og.get("plik") or "", "alt": og.get("alt") or ""}
    seo["schemat"] = seo.get("schemat") or []
    d["seo"] = seo
    d["geo"] = {"streszczenie": (d.get("geo") or {}).get("streszczenie") or ""}
    d["sekcje"] = d.get("sekcje") or []
    d["wejscie"]["bloki"] = d["wejscie"].get("bloki") or []
    for s in d["sekcje"]:
        s["bloki"] = s.get("bloki") or []
    return d

strony = {p.stem: uzupelnij(yaml.safe_load(p.read_text(encoding="utf-8"))) for p in sorted((C / "strony").glob("*.yml"))}
# Strony kampanii (od 19.11.2026): poza menu, mapą strony i llms.txt; adres w polu „adres” bez ukośnika.
kampanie = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) or {} for p in sorted((C / "kampanie").glob("*.yml"))}
PODGLAD = "--podglad" in sys.argv[1:]

bledy, uwagi, zaslepki = [], [], []
def blad(m): bledy.append(m)
def uwaga(m): uwagi.append(m)

# ------------------------------------------------ 1. każde pole treści ma pole w CMS

def pola_cfg(kolekcja, plik=None):
    """Pola z konfiguracji CMS: plik kolekcji plików, pojedynczy wpis (kolekcja „_singletons”) albo kolekcja folderu."""
    if kolekcja == "_singletons":
        for f in cfg.get("singletons") or []:
            if f.get("name") == plik:
                return f["fields"]
        raise KeyError(plik)
    for col in cfg["collections"]:
        if col.get("name") == kolekcja:
            if plik is None:
                return col["fields"]
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
sprawdz_pokrycie({"pytania": baza}, pola_cfg("_singletons", "pytania"), "baza")
sprawdz_pokrycie(ust, pola_cfg("_singletons", "wspolne"), "ustawienia")
for nazwa, d in kampanie.items():
    sprawdz_pokrycie(d, pola_cfg("kampanie"), f"kampania {nazwa}")
cfg_pliki = {f["name"] for col in cfg["collections"] if col.get("name") == "strony" for f in col["files"]}
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

ZAKAZANE = [r"senior\w*", r"podopieczn\w*", r"złot\w+ jesie\w*", r"jesie\w* życia", r"srebrn\w+ gospodar\w*",
            r"aktywizac\w*", r"monitoring\w*", r"monitoruj\w*", r"kontrol\w*", r"nadz[oó]r\w*", r"opiekun\w*",
            r"kompleksow\w*", r"dedykowan\w*", r"innowacyjn\w*", r"nowoczesn\w*", r"rewolucyjn\w*"]
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
for nazwa, d in kampanie.items():
    for sc, tx in widoczne_teksty(nazwa, d):
        if sc != "nazwa_robocza":
            skanuj(f"kampania {nazwa}", sc, tx)
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
# Strony bez pliku treści, które buduje szablon (na adresie tymczasowym „w przygotowaniu”): link do nich jest poprawny.
STRONY_SZABLONU = {"/regulamin-strony", "/regulamin-uslugi", "/prywatnosc"}
# Strony, których jeszcze nie ma (zamówienie w panelu klienta): link zostaje nieaktywny.
DO_ZBUDOWANIA = {"/umow"}
WSZYSTKIE_PYTANIA = ust["nawigacja"]["wszystkie_pytania"]

def sprawdz_link(zrodlo, adres, tekst=None, aktywny=True):
    """Link istnieje, a jego tekst to nazwa strony albo rozdziału, do którego prowadzi (jeden temat, jedna nazwa)."""
    if not aktywny or not adres or adres.startswith("http"):
        return
    sciezka, _, kot = adres.partition("#")
    sciezka = sciezka or "/"
    if sciezka in STRONY_SZABLONU:
        return
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
            for k, pk in enumerate(bl.get("punkty") or []):
                if not isinstance(pk, str):
                    blad(f"{gdzie}: punkt {k + 1} nie jest tekstem (dwukropek ze spacją w punkcie bez cudzysłowu)")
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

def sprawdz_strone(n, d, kampania=False):
    seo = d.get("seo") or {}
    lt, lo = len(seo.get("tytul") or ""), len(seo.get("opis") or "")
    if kampania and not 10 <= lt <= 70:
        blad(f"{n}: tytuł ma {lt} znaków (10–70)")
    if seo.get("indeksuj"):
        if lt > 70: blad(f"{n}: tytuł ma {lt} znaków (maks. 70)")
        elif lt > 60: uwaga(f"{n}: tytuł ma {lt} znaków (zalecane do 60)")
        if not 110 <= lo <= 160: blad(f"{n}: opis ma {lo} znaków (110–160)")
        elif lo > 155: uwaga(f"{n}: opis ma {lo} znaków (zalecane do 155)")
        if not kampania and not d["geo"]["streszczenie"]:
            blad(f"{n}: brak streszczenia dla AI")
    w = d.get("wejscie") or {}
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
    for i, sek in enumerate(d.get("sekcje") or []):
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

    if kampania:
        for i, sek in enumerate([w] + list(d.get("sekcje") or [])):
            for bl in sek.get("bloki") or []:
                if bl.get("typ") == "pytania":
                    blad(f"{n}: karty pytań stoją tylko na stronie Pytania; na stronie kampanii użyj akordeonu „Najczęstsze pytania”")

for n, d in strony.items():
    sprawdz_strone(n, d)
for n, d in kampanie.items():
    sprawdz_strone(f"kampania {n}", d, kampania=True)

for q in baza:
    if q.get("link"):
        ln = q.get("link") or {}
        sprawdz_link(f"baza · {q['id']}", ln.get("adres"), ln.get("tekst"))
for l in ust["nawigacja"]["strony"]:
    sprawdz_link("nawigacja", l["adres"], l["tekst"])
for l in ust["naglowek"]["linki"]:
    sprawdz_link("belka górna", l["adres"], l["tekst"])
for l in ust["stopka"]["linki_prawne"]:
    sprawdz_link("stopka", l["adres"])
for r in ust["stopka"]["wezwania"]:
    if r not in ust["wezwania"]:
        blad(f"stopka: nieznany przycisk {r!r}")
# Adres strony kampanii: własny, niepowtarzalny, nie zajmuje adresu strony z menu ani strony budowanej przez szablon.
ZAJETE = set(adresy) | STRONY_SZABLONU | DO_ZBUDOWANIA | {"/sprawdzenie", "/admin", "/robots.txt", "/llms.txt",
                                                          "/llms-full.txt", "/sitemap-index.xml", "/sitemap-0.xml"}
adresy_kampanii = {}
for n, d in kampanie.items():
    a = d.get("adres") or ""
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a):
        blad(f"kampania {n}: adres „{a}” – małe litery bez polskich znaków, cyfry i łącznik")
        continue
    if "/" + a in ZAJETE:
        blad(f"kampania {n}: adres /{a} ma już inna strona")
    if a in adresy_kampanii:
        blad(f"kampania {n}: adres /{a} ma już kampania {adresy_kampanii[a]}")
    adresy_kampanii[a] = n

if set(adresy) - {"/404"} != set(nazwy_stron.values()):
    blad(f"Lista stron w nawigacji i pliki stron się różnią: {sorted((set(adresy) - {'/404'}) ^ set(nazwy_stron.values()))}")

# ------------------------------------------------ 4a. teksty alternatywne zdjęć

ALT_ZAKAZ = re.compile(r"\b(Arthur\w*|arthurozm\w*|AI|SI|sztuczn\w+ inteligenc\w+)\b", re.IGNORECASE)
for n, d in list(strony.items()) + [(f"kampania {k}", v) for k, v in kampanie.items()]:
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
# Jednostką jest tydzień (16.11.2026): liczby rozmów w tygodniu muszą stać w polu „rytm” (zero się pomija).
for p in ust["pakiety"]["lista"]:
    for pole in ("rozmowy_pelne", "rozmowy_podtrzymujace"):
        if p[pole] and str(p[pole]) not in p["rytm"]:
            blad(f"Pakiet {p['cena']} zł: liczba w polu {pole} ({p[pole]}) nie zgadza się z rytmem „{p['rytm']}”")

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
# Strony kampanii: bez zasady liczby zdjęć; plik musi istnieć i mieć format układu wejścia (1:1 albo 21:9 z kadrem 4:3).
for k, d in kampanie.items():
    n = f"kampania {k}"
    szablon = (d.get("strona") or {}).get("szablon") or "podstrona"
    we = (d.get("wejscie") or {}).get("zdjecie") or {}
    zz = ([("wejscie", we)] if we.get("plik") else []) + [("rozdzial", s["zdjecie"]) for s in d.get("sekcje") or [] if (s.get("zdjecie") or {}).get("plik")]
    for miejsce, z in zz:
        pliki_zdjec.setdefault(z["plik"].rsplit("/", 1)[-1], n)
        widoczne = bool(z.get("widoczne", True))
        if miejsce == "wejscie" and szablon == "glowna":
            sprawdz_plik(n, z["plik"], "21x9", widoczne)
            if z.get("plik_telefon"):
                sprawdz_plik(n, z["plik_telefon"], "4x3", widoczne)
            else:
                blad(f"{n}: wejście z układem „jak strona główna” bez kadru 4:3 na telefon")
        else:
            sprawdz_plik(n, z["plik"], "1x1" if miejsce == "wejscie" else "4x3", widoczne)
uzywane = set(pliki_zdjec) | {((d.get("wejscie") or {}).get("zdjecie") or {}).get("plik_telefon", "").rsplit("/", 1)[-1]
                              for d in list(strony.values()) + list(kampanie.values())}
for plik in sorted((ROOT / "public/images/strony").glob("*")):
    if plik.name not in uzywane:
        uwaga(f"public/images/strony/{plik.name}: plik nie stoi na żadnej stronie (do usunięcia)")

# ------------------------------------------------ raport

def wypisz(tytul, lista):
    print(f"\n{tytul} ({len(lista)})")
    for x in lista:
        print("  -", x)

def raport_podgladu():
    """Strona /sprawdzenie i podsumowanie dla plakietki: tylko w podglądzie wersji roboczej (opcja --podglad)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    linki = {n: d["seo"]["adres"] for n, d in strony.items()}
    linki.update({f"kampania {n}": "/" + (d.get("adres") or "") for n, d in kampanie.items()})
    linki["baza"] = "/pytania"

    def pozycja(tx):
        glowa, sep, reszta = tx.partition(" · ")
        if not sep:
            glowa, sep, reszta = tx.partition(": ")
        adres = linki.get(glowa)
        if adres:
            return f'<li><a href="{html.escape(adres)}">{html.escape(glowa)}</a>{html.escape(sep + reszta)}</li>'
        return f"<li>{html.escape(tx)}</li>"

    def grupa(tytul, klasa, lista, pusto):
        tresc = "".join(pozycja(x) for x in lista) if lista else f"<li class=\"pusto\">{pusto}</li>"
        return f'<section class="{klasa}"><h2>{tytul} ({len(lista)})</h2><ul>{tresc}</ul></section>'

    czas = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y, %H:%M")
    stan = ("Ta wersja ma błędy i nie trafi na witrynę, dopóki ich nie poprawisz." if bledy
            else "Błędów nie ma: tę wersję można opublikować.")
    strona = f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Sprawdzenie treści · podgląd</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bona+Nova:wght@700&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root{{--papier:#F2EFE6;--onyks:#0B0C10;--mech:#48594F;--rdza:#B3562E;--piasek:#DBD2C3;--jajko:#FFDE59}}
body{{margin:0;background:var(--papier);color:var(--onyks);font:17px/1.55 "IBM Plex Sans",system-ui,sans-serif}}
main{{max-width:52rem;margin:0 auto;padding:40px max(16px,env(safe-area-inset-left)) 64px}}
h1{{font:700 2rem/1.2 "Bona Nova",Georgia,serif;color:var(--mech);margin:0 0 .4rem}}
h2{{font-size:1rem;letter-spacing:.1em;text-transform:uppercase;margin:2rem 0 .6rem;color:var(--mech)}}
.stan{{font-weight:600;padding:12px 16px;border-radius:0 0 24px 0;background:var(--piasek)}}
.stan.zle{{background:var(--rdza);color:#fff}}
ul{{margin:0;padding-left:1.2rem;display:grid;gap:.45rem}}
.bledy li:not(.pusto){{color:var(--rdza)}} .pusto{{list-style:none;margin-left:-1.2rem;color:var(--mech)}}
a{{color:inherit;border:1px solid var(--rdza);border-radius:30px;padding:0 .45em;text-decoration:none}}
.meta{{color:var(--mech);font-size:.9rem}}
</style></head><body><main>
<h1>Sprawdzenie treści</h1>
<p class="meta">Podgląd wersji roboczej · {czas}. Ta strona jest tylko w podglądzie i nie ma jej na witrynie.</p>
<p class="stan{' zle' if bledy else ''}">{stan}</p>
{grupa("Błędy", "bledy", bledy, "Brak błędów.")}
{grupa("Uwagi", "uwagi", uwagi, "Brak uwag.")}
{grupa("Zaślepki: strona z zaślepką nie wychodzi na arthurozmowy.pl", "zaslepki", zaslepki, "Brak zaślepek.")}
<p class="meta"><a href="/">Wróć na stronę główną podglądu</a></p>
</main></body></html>
"""
    (ROOT / "public" / "sprawdzenie.html").write_text(strona, encoding="utf-8")
    (ROOT / ".sprawdzenie.json").write_text(json.dumps(
        {"bledy": len(bledy), "uwagi": len(uwagi), "zaslepki": len(zaslepki)}), encoding="utf-8")

wypisz("BŁĘDY", bledy)
wypisz("UWAGI", uwagi)
wypisz("ZAŚLEPKI (strona z zaślepką nie wychodzi)", zaslepki)
print(f"\nStrony: {len(strony)}, strony kampanii: {len(kampanie)}, pytania w bazie: {len(baza)}.")
if PODGLAD:
    raport_podgladu()
    print("Podgląd: zapisano public/sprawdzenie.html i .sprawdzenie.json.")
    sys.exit(0)
sys.exit(1 if bledy else 0)
