#!/usr/bin/env python3
"""Buduje pliki pochodne z treści arthurozmowy.pl.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/buduj_pochodne.py
Powstają:
  docs/podglad/<strona>.md   tekst strony w kolejności wyświetlania, z nazwą modułu i pola CMS przy każdym elemencie
  docs/mapa-pol.md           mapa: strona → rozdział → bloki (moduły makiety) → pola w CMS
  docs/jsonld/<strona>.json  dane strukturalne, które szablon Astro wstawia w <script type="application/ld+json">
  docs/lista-grafik.md       pliki graficzne: miejsce, nazwa, alt, format, stan
  public/llms.txt            streszczenie witryny dla modeli AI (llmstxt.org)
  public/llms-full.txt       pełne teksty widocznych stron bez zaślepek
"""
from pathlib import Path
import json, re
import yaml

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "src" / "content"
ust = yaml.safe_load((C / "ustawienia/witryna.yml").read_text(encoding="utf-8"))
baza = {q["id"]: q for q in yaml.safe_load((C / "pytania/baza.yml").read_text(encoding="utf-8"))["pytania"]}
wczytane = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in (C / "strony").glob("*.yml")}
po_adresie = {d["seo"]["adres"]: n for n, d in wczytane.items()}
# Kolejność stron jak w menu (nawigacja.strony), na końcu strona błędu.
KOLEJNOSC = [po_adresie[l["adres"]] for l in ust["nawigacja"]["strony"] if l["adres"] in po_adresie]
KOLEJNOSC += [n for n in sorted(wczytane) if n not in KOLEJNOSC]
strony = {n: wczytane[n] for n in KOLEJNOSC}
GLOWNA = po_adresie["/"]

DOM = ust["marka"]["domena"].rstrip("/")
F = ust["firma"]
FIRMA = f"{F['nazwa']}, {F['ulica']}, {F['kod_pocztowy']} {F['miejscowosc']}, NIP {F['nip']}"
W = ust["wezwania"]
ZNACZNIKI = {"{firma}": FIRMA, "{email}": F["email"], "{telefon}": F["telefon"], "{godziny}": F["telefon_godziny"]}

def rozwin(tx):
    tx = tx or ""
    for znacznik, wartosc in ZNACZNIKI.items():
        tx = tx.replace(znacznik, wartosc)
    return tx

def czysty(tx):
    """Markdown → zwykły tekst (do JSON-LD i llms-full.txt)."""
    tx = rozwin(tx)
    tx = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tx)
    tx = tx.replace("**", "")
    return re.sub(r"\n{2,}", "\n\n", tx).strip()

def wielka(tx):
    return tx[:1].upper() + tx[1:]

ZASLEPKA = re.compile(r"\[(?!\s*\])[^\]]+\](?!\()")
MODULY = {"tekst": "Tekst akapitu", "glos": "Voice aside", "lista": "Lista", "zasady": "Zasady (H3)", "cytat": "Karta cytatu",
          "cennik": "Karty ceny", "link": "Link wewnętrzny", "wezwanie": "Przycisk CTA", "pytania": "Karty pytań",
          "faq": "Najczęstsze pytania (akordeon)"}
CEL_WEZWANIA = {"glowne": "okienko „Porozmawiaj z Arthurem”", "zakupowe": "zamówienie w panelu klienta",
                "napisz": "okienko „Napisz do nas”"}

def repliki_txt(bl):
    out = []
    for r in bl.get("repliki") or []:
        kto = f"{r['kto']}: " if r.get("kto") else ""
        out.append(f"{kto}„{r['kwestia']}”")
    return out

# ------------------------------------------------ podgląd strony

def zdjecie_md(z, pref):
    if not z or not z.get("plik"):
        return []
    pliki = f"`{z['plik']}`" + (f" · telefon: `{z['plik_telefon']}`" if z.get("plik_telefon") else "")
    stan = "" if z.get("widoczne") else " *(ukryte)*"
    return [f"**Plik graficzny:** {pliki}{stan}  `{pref}`", "", f"**Alt:** {z.get('alt') or '—'}  `{pref}.alt`", ""]

def bloki_md(bloki, pref):
    o = []
    for j, bl in enumerate(bloki or []):
        p, typ = f"{pref}[{j}]", bl["typ"]
        o += [f"**{MODULY[typ]}** `{p}`", ""]
        if typ in ("tekst", "glos"):
            o += [rozwin(bl["tekst"]), ""]
        elif typ == "lista":
            if bl.get("naglowek"):
                o += [bl["naglowek"], ""]
            o += [f"{k + 1}. {x}" if bl.get("numerowana") else f"- {x}" for k, x in enumerate(bl["punkty"])] + [""]
        elif typ == "zasady":
            for k, z in enumerate(bl["zasady"]):
                o += [f"### {k + 1}. {z['naglowek']}", "", f"*{z.get('lid', '')}*", "", z.get("tekst", ""), ""]
        elif typ == "cytat":
            if not bl.get("widoczny", True):
                o += ["*(karta ukryta)*", ""]
            if bl.get("etykieta"):
                o += [f"*{bl['etykieta']}*", ""]
            if bl.get("wstep"):
                o += [bl["wstep"], ""]
            o += [f"> {x}  " for x in repliki_txt(bl)] + [""]
        elif typ == "cennik":
            o += [f"- {wielka(pk['nazwa'])} – {pk['cena']} zł {ust['pakiety']['okres']}: {pk['opis']}" for pk in ust["pakiety"]["lista"]]
            o += ["", "*Pakiety z Ustawień → Pakiety i ceny*", ""]
        elif typ == "link":
            stan = "" if bl.get("aktywny", True) else " *(nieaktywny)*"
            o += [f"{bl['tekst']} → {bl.get('adres') or '—'}{stan}", ""]
        elif typ == "wezwanie":
            o += [f"{W[bl['rodzaj']]['przycisk']} → {CEL_WEZWANIA[bl['rodzaj']]}", ""]
            if bl.get("objasnienie"):
                o += [f"*Objaśnienie pod przyciskiem:* {W['glowne']['dopisek']}", ""]
        elif typ == "pytania":
            for pid in bl["pytania"]:
                q = baza[pid]
                o += [f"### {q['pytanie']}  `baza:{pid}`", "", rozwin(q["odpowiedz"]), ""]
                if q.get("link"):
                    o += [f"**Link wewnętrzny:** {q['link']['tekst']} → {q['link']['adres']}", ""]
        elif typ == "faq":
            o += [f"- {baza[pid]['pytanie']}  `baza:{pid}`" for pid in bl["pytania"]]
            o += ["", f"**Link wewnętrzny:** {ust['nawigacja']['wszystkie_pytania']} → /pytania", ""]
    return o

def podglad(n, d):
    seo, w = d["seo"], d["wejscie"]
    o = [f"# {d['strona']['nazwa']} · {seo['adres']}", "",
         f"*Plik: `src/content/strony/{n}.yml` · szablon: {d['strona']['szablon']} · "
         f"aktualizacja: {seo['zaktualizowano']} · autor: {seo['autor']}*", "",
         "## Metryczka warstwy wyszukiwarki", "",
         f"- **Tytuł strony ({len(seo['tytul'])} zn.):** {seo['tytul']}  `seo.tytul`",
         f"- **Opis w wynikach ({len(seo['opis'])} zn.):** {seo['opis'] or '—'}  `seo.opis`",
         f"- **Obraz do udostępniania:** `{seo['obraz_og']['plik'] or '—'}` · alt: {seo['obraz_og']['alt'] or '—'}  `seo.obraz_og`",
         f"- **Dane dla wyszukiwarek:** {', '.join(seo['schemat']) or '—'}  `seo.schemat`",
         f"- **W wyszukiwarkach:** {'tak' if seo['indeksuj'] else 'nie (noindex)'}  `seo.indeksuj`",
         f"- **Streszczenie dla AI:** {d['geo']['streszczenie'] or '—'}  `geo.streszczenie`", "",
         "## Wejście" + (f" · #{w['kotwica']} · w spisie treści: „{w['etykieta']}”" if w.get("etykieta") else ""), "",
         f"**Nazwa strony:** {d['strona']['nazwa'].upper()}  `strona.nazwa`", ""]
    o += zdjecie_md(w.get("zdjecie"), "wejscie.zdjecie")
    o += [f"**Nagłówek H1** `wejscie.h1`", "", w["h1"], ""]
    if w.get("lid"):
        o += ["**Lid H1** `wejscie.lid`", "", rozwin(w["lid"]), ""]
    if w.get("przycisk_powrotu"):
        o += [f"**Przycisk powrotu:** {w['przycisk_powrotu']['tekst']} → {w['przycisk_powrotu']['adres']}  `wejscie.przycisk_powrotu`", ""]
    o += bloki_md(w.get("bloki"), "wejscie.bloki")
    for i, s in enumerate(d.get("sekcje") or []):
        p = f"sekcje[{i}]"
        nag = f"## {i + 1}. {s.get('etykieta') or '(poza spisem treści)'}"
        if s.get("kotwica"):
            nag += f" · #{s['kotwica']}"
        o += [nag + f" · ton {s.get('ton')}", "", f"**Nagłówek H2** `{p}.h2`", "", s.get("h2") or "—", ""]
        o += zdjecie_md(s.get("zdjecie"), f"{p}.zdjecie")
        if s.get("lid"):
            o += [f"**Lid H2** `{p}.lid`", "", rozwin(s["lid"]), ""]
        o += bloki_md(s.get("bloki"), f"{p}.bloki")
    return "\n".join(o).rstrip() + "\n"

out_p = ROOT / "docs" / "podglad"
out_p.mkdir(parents=True, exist_ok=True)
for stary in out_p.glob("*.md"):
    stary.unlink()
for n, d in strony.items():
    (out_p / f"{n}.md").write_text(podglad(n, d), encoding="utf-8")

# ------------------------------------------------ mapa pól

def skrot_blokow(bloki):
    return ", ".join(MODULY[b["typ"]] + (f" ({W[b['rodzaj']]['przycisk']})" if b["typ"] == "wezwanie" else "") for b in bloki or []) or "—"

m = ["# Mapa pól: strona → rozdział → bloki → pole w CMS", "",
     "*Plik generowany przez narzedzia/buduj_pochodne.py. Jeden blok to jeden moduł makiety V2. "
     "Ścieżka pola odpowiada kluczom w pliku strony i polom w Sveltia CMS.*", ""]
for n, d in strony.items():
    w = d["wejscie"]
    m += [f"## {d['strona']['nazwa']} · `{d['seo']['adres']}` · `src/content/strony/{n}.yml`", "",
          "| Nr | Rozdział (spis treści) | Kotwica | Zdjęcie | Lid | Bloki w kolejności |", "|---|---|---|---|---|---|",
          f"| 0 | {w.get('etykieta') or 'Wejście'} | {('#' + w['kotwica']) if w.get('kotwica') else '—'} | "
          f"{'tak' if (w.get('zdjecie') or {}).get('plik') else '—'} | {'tak' if w.get('lid') else '—'} | {skrot_blokow(w.get('bloki'))} |"]
    for i, s in enumerate(d.get("sekcje") or []):
        m += [f"| {i + 1} | {s.get('etykieta') or '(poza spisem)'} | {('#' + s['kotwica']) if s.get('kotwica') else '—'} | "
              f"{'tak' if (s.get('zdjecie') or {}).get('plik') else '—'} | {'tak' if s.get('lid') else '—'} | {skrot_blokow(s.get('bloki'))} |"]
    m += [""]
m += ["## Ustawienia wspólne · `src/content/ustawienia/witryna.yml`", "",
      "| Grupa | Co zawiera | Gdzie się pokazuje |", "|---|---|---|",
      "| `marka` | nazwa, domena, definicja, logo | belka górna, JSON-LD, llms.txt, odpowiedź „Czym są arthurozmowy?” |",
      "| `naglowek` | napisy menu, linki w belce, przycisk zamówienia, Panel klienta | belka górna każdej strony |",
      "| `nawigacja` | jedna lista stron z nazwami i adresami, napis „Wszystkie pytania” | menu, stopka, akordeony pytań |",
      "| `wezwania` | trzy przyciski CTA: rozmowa, zamówienie, kontakt | bloki „Przycisk CTA” i stopka |",
      "| `okno_rozmowy`, `okno_kontaktu` | teksty dwóch okienek z formularzami | okienka otwierane przyciskami CTA |",
      "| `pakiety` | ceny, liczby rozmów, opisy | karty ceny, JSON-LD Offer, llms.txt |",
      "| `firma` | dane firmy i kontaktowe | znaczniki {firma}, {email}, {telefon}, {godziny}, stopka, JSON-LD |",
      "| `stopka` | przyciski CTA, zdanie o statystykach, dane firmy, linki prawne | stopka każdej strony |", "",
      "## Baza pytań · `src/content/pytania/baza.yml`", "",
      "| Identyfikator | Pytanie | Rozdział na stronie Pytania | Akordeony na podstronach |", "|---|---|---|---|"]
uzycie, rozdzial = {}, {}
for n, d in strony.items():
    for s in d.get("sekcje") or []:
        for bl in s.get("bloki") or []:
            if bl["typ"] == "faq":
                for pid in bl["pytania"]:
                    uzycie.setdefault(pid, []).append(d["strona"]["nazwa"])
            if bl["typ"] == "pytania":
                for pid in bl["pytania"]:
                    rozdzial[pid] = s.get("etykieta") or "—"
for pid, q in baza.items():
    m += [f"| `{pid}` | {q['pytanie']} | {rozdzial.get(pid, '—')} | {', '.join(uzycie.get(pid, [])) or '—'} |"]
(ROOT / "docs" / "mapa-pol.md").write_text("\n".join(m) + "\n", encoding="utf-8")

# ------------------------------------------------ JSON-LD

ORG_ID, WEB_ID, USL_ID, OS_ID = f"{DOM}/#organizacja", f"{DOM}/#witryna", f"{DOM}/#usluga", f"{DOM}/o-nas#piotr-jaworski"
nip = re.sub(r"\D", "", F["nip"])
strona_ceny = next((d["seo"]["adres"] for n, d in strony.items() if n != GLOWNA
                    and any(s.get("kotwica") == "cena" for s in d.get("sekcje") or [])), "/")
org = {"@type": "Organization", "@id": ORG_ID, "name": F["nazwa"], "url": DOM + "/",
       "logo": DOM + ust["marka"]["logo"]["plik"], "email": F["email"], "telephone": F["telefon"].replace(" ", ""),
       "taxID": nip,
       "address": {"@type": "PostalAddress", "streetAddress": F["ulica"], "postalCode": F["kod_pocztowy"],
                   "addressLocality": F["miejscowosc"], "addressCountry": F["kraj"]},
       "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "email": F["email"],
                        "telephone": F["telefon"].replace(" ", ""), "availableLanguage": "pl"},
       "founder": {"@id": OS_ID}}
witryna = {"@type": "WebSite", "@id": WEB_ID, "url": DOM + "/", "name": ust["marka"]["nazwa"],
           "inLanguage": ust["marka"]["jezyk"], "publisher": {"@id": ORG_ID}}
oferty = [{"@type": "Offer", "name": f"{wielka(p['nazwa'])}: {p['cena']} zł miesięcznie, {p['opis']}",
           "price": str(p["cena"]), "priceCurrency": ust["pakiety"]["waluta"],
           "priceSpecification": {"@type": "UnitPriceSpecification", "price": p["cena"],
                                  "priceCurrency": ust["pakiety"]["waluta"], "unitCode": "MON",
                                  "valueAddedTaxIncluded": True},
           "url": DOM + strona_ceny + "#cena", "seller": {"@id": ORG_ID}}
          for p in ust["pakiety"]["lista"]]
usluga = {"@type": "Service", "@id": USL_ID, "name": ust["marka"]["nazwa"], "serviceType": "Rozmowy telefoniczne z programem AI",
          "description": ust["marka"]["definicja"], "provider": {"@id": ORG_ID}, "areaServed": "PL",
          "availableLanguage": "pl", "offers": oferty}
osoba = {"@type": "Person", "@id": OS_ID, "name": ust["autor"]["imie_nazwisko"], "url": DOM + "/o-nas",
         "worksFor": {"@id": ORG_ID}}

def strona_ld(d, typ="WebPage"):
    seo = d["seo"]
    return {"@type": typ, "@id": DOM + seo["adres"] + "#strona", "url": DOM + seo["adres"], "name": seo["tytul"],
            "description": seo["opis"], "inLanguage": ust["marka"]["jezyk"], "isPartOf": {"@id": WEB_ID},
            "about": {"@id": USL_ID}, "dateModified": str(seo["zaktualizowano"]), "author": {"@id": OS_ID},
            **({"primaryImageOfPage": DOM + seo["obraz_og"]["plik"]} if seo["obraz_og"]["plik"] else {})}

def okruszki(d):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": strony[GLOWNA]["strona"]["nazwa"], "item": DOM + "/"},
        {"@type": "ListItem", "position": 2, "name": d["strona"]["nazwa"], "item": DOM + d["seo"]["adres"]}]}

def tekst_rozdzialu(s):
    """Lid i teksty akapitów rozdziału jako zwykły tekst (krok HowTo)."""
    czesci = [czysty(s.get("lid"))] + [czysty(b["tekst"]) for b in s.get("bloki") or [] if b["typ"] == "tekst"]
    return " ".join(c for c in czesci if c)

out_j = ROOT / "docs" / "jsonld"
out_j.mkdir(parents=True, exist_ok=True)
for stary in out_j.glob("*.json"):
    stary.unlink()
for n, d in strony.items():
    sch = set(d["seo"]["schemat"])
    graf = []
    if not d["seo"]["indeksuj"]:
        continue
    typ_strony = "AboutPage" if "AboutPage" in sch else "ContactPage" if "ContactPage" in sch else \
        "FAQPage" if "FAQPage" in sch else "WebPage"
    if typ_strony == "FAQPage":
        faq = strona_ld(d, "FAQPage")
        faq["mainEntity"] = [{"@type": "Question", "name": baza[pid]["pytanie"],
                              "acceptedAnswer": {"@type": "Answer", "text": czysty(baza[pid]["odpowiedz"])}}
                             for s in d["sekcje"] for bl in s.get("bloki") or [] if bl["typ"] == "pytania" for pid in bl["pytania"]]
        graf.append(faq)
    else:
        graf.append(strona_ld(d, typ_strony))
    if "Organization" in sch: graf.append(org)
    if "WebSite" in sch: graf.append(witryna)
    if "Service" in sch or "Offer" in sch: graf.append(usluga)
    if "Person" in sch: graf.append(osoba)
    if "HowTo" in sch:
        kroki = [s for s in d["sekcje"] if s.get("etykieta")]
        graf.append({"@type": "HowTo", "name": d["wejscie"]["h1"], "description": czysty(d["wejscie"].get("lid")),
                     "inLanguage": ust["marka"]["jezyk"],
                     "step": [{"@type": "HowToStep", "position": k + 1, "name": s["h2"],
                               "text": tekst_rozdzialu(s), "url": DOM + d["seo"]["adres"] + "#" + s["kotwica"]}
                              for k, s in enumerate(kroki)]})
    if "BreadcrumbList" in sch: graf.append(okruszki(d))
    (out_j / f"{n}.json").write_text(json.dumps({"@context": "https://schema.org", "@graph": graf},
                                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ------------------------------------------------ llms.txt i llms-full.txt

g = strony[GLOWNA]
l = [f"# {ust['marka']['nazwa']}", "", f"> {ust['marka']['definicja']}", "",
     g["geo"]["streszczenie"], "",
     "Najważniejsze fakty:", "",
     f"- Usługę świadczy firma {FIRMA}.",
     "- Usługę zamawia i opłaca dorosłe dziecko, a z Arthurem rozmawia jego mama, tylko za swoją zgodą.",
     "- Arthur jest programem opartym na sztucznej inteligencji i nigdy nie udaje człowieka; „h” w imieniu to „h” jak humanoid.",
     "- Pakiety: " + "; ".join(f"{p['nazwa']} {p['cena']} zł miesięcznie z VAT: {p['opis']}" for p in ust["pakiety"]["lista"]) + ".",
     "- Pierwszy, próbny miesiąc jest bezpłatny. Rezygnacja jednym kliknięciem uruchamia 15-dniowe „Pożegnanie”.",
     "- Granice: Arthur nie zastępuje pomocy w domu, przycisku SOS ani lekarza, nie wie, co dzieje się u mamy między rozmowami, "
     "nie diagnozuje i nie obiecuje ochrony przed demencją.", "",
     "## Strony", ""]
for n, d in strony.items():
    if n == GLOWNA or not d["seo"]["indeksuj"]:
        continue
    l.append(f"- [{d['strona']['nazwa']}]({DOM}{d['seo']['adres']}): {d['geo']['streszczenie']}")
l += ["", "## Pełne teksty", "", f"- [Wszystkie teksty witryny w jednym pliku]({DOM}/llms-full.txt)", ""]
(ROOT / "public" / "llms.txt").write_text("\n".join(l), encoding="utf-8")

def bloki_txt(bloki):
    o = []
    for bl in bloki or []:
        typ = bl["typ"]
        if typ in ("tekst", "glos"):
            o += ["", czysty(bl["tekst"])]
        elif typ == "lista":
            o += [""] + ([bl["naglowek"]] if bl.get("naglowek") else [])
            o += [f"{k + 1}. {x}" if bl.get("numerowana") else f"- {x}" for k, x in enumerate(bl["punkty"])]
        elif typ == "zasady":
            for k, z in enumerate(bl["zasady"]):
                o += ["", f"{k + 1}. {z['naglowek']} {z.get('lid', '')} {z.get('tekst', '')}".strip()]
        elif typ == "cytat" and bl.get("widoczny", True):
            o += [""] + ([bl["etykieta"] + ":"] if bl.get("etykieta") else []) + ([bl["wstep"]] if bl.get("wstep") else [])
            o += [f"- {x}" for x in repliki_txt(bl)]
        elif typ == "cennik":
            o += [""] + [f"- {wielka(p['nazwa'])} – {p['cena']} zł {ust['pakiety']['okres']}: {p['opis']}" for p in ust["pakiety"]["lista"]]
        elif typ == "pytania":
            for pid in bl["pytania"]:
                o += ["", "#### " + baza[pid]["pytanie"], "", czysty(baza[pid]["odpowiedz"])]
    return o

pelne = [f"# {ust['marka']['nazwa']} · pełne teksty witryny", "", f"> {ust['marka']['definicja']}", ""]
pominiete = []
for n, d in strony.items():
    if not d["seo"]["indeksuj"]:
        continue
    w = d["wejscie"]
    blok = [f"## {d['seo']['tytul']}", f"{DOM}{d['seo']['adres']}", "", czysty(w["h1"]), "", czysty(w.get("lid"))] + bloki_txt(w.get("bloki"))
    for s in d.get("sekcje") or []:
        if all(b["typ"] in ("faq", "link", "wezwanie") for b in s.get("bloki") or []) and not s.get("lid"):
            continue   # akordeon powtarza odpowiedzi ze strony Pytania
        blok += ["", "### " + czysty(s["h2"])]
        if s.get("lid"):
            blok += ["", czysty(s["lid"])]
        blok += bloki_txt(s.get("bloki"))
    tekst = "\n".join(blok)
    if ZASLEPKA.search(tekst):
        pominiete.append(n)
        continue
    pelne += [tekst, ""]
(ROOT / "public" / "llms-full.txt").write_text("\n".join(pelne), encoding="utf-8")

# ------------------------------------------------ lista grafik

# Zasada: strona główna ma 4 zdjęcia (wejście i 3 w rozdziałach), każda podstrona 2 (wejście i 1 w rozdziale), strona 404 żadnego.
# Nowa treść zdjęcia = nowa nazwa pliku. Stan wynika z plików w public/images.
PUB = ROOT / "public"
def jest(sciezka):
    return bool(sciezka) and (PUB / sciezka.lstrip("/")).is_file()
FMT = {"21x9": "21:9 (komputer) i kadr 4:3 · 1200 × 900 (telefon)", "1x1": "1:1 · 1200 × 1200", "4x3": "4:3 · 1200 × 900"}

wiersze = []
for n, d in strony.items():
    hero = d["strona"]["szablon"] == "glowna"
    miejsca = [("wejście (H1)", d["wejscie"].get("zdjecie") or {}, "21x9" if hero else "1x1")]
    miejsca += [(s.get("etykieta") or s.get("kotwica"), s.get("zdjecie") or {}, "4x3") for s in d.get("sekcje") or []]
    nr = 0
    for miejsce, z, fmt in miejsca:
        if not z.get("plik"):
            continue
        nr += 1
        pliki = z["plik"].rsplit("/", 1)[-1] + (" i " + z["plik_telefon"].rsplit("/", 1)[-1] if z.get("plik_telefon") else "")
        gotowe = jest(z["plik"]) and (not z.get("plik_telefon") or jest(z["plik_telefon"]))
        stan = ("gotowe" + ("" if z.get("widoczne") else ", na stronie ukryte")) if gotowe else "brak pliku"
        wiersze.append((d["strona"]["nazwa"], nr, miejsce, pliki, z.get("alt", ""), FMT[fmt], stan))

lg = ["# Zdjęcia witryny arthurozmowy.pl", "",
      "*Plik generowany przez narzedzia/buduj_pochodne.py z plików stron. Zasada: strona główna ma 4 zdjęcia (wejście i 3 w rozdziałach), "
      "każda podstrona 2 (wejście i 1 w rozdziale), strona 404 żadnego. Nowa treść zdjęcia dostaje nową nazwę pliku. "
      "Pliki są w `public/images/strony/` i nazywają się `arthurozmowy-{strona}-{treść}-{format}.webp`: wejście strony głównej 21x9 "
      "z osobnym kadrem 4x3 na telefon, wejście podstrony 1x1, zdjęcie w rozdziale 4x3. "
      "Alt: co naprawdę widać, słowami strony, nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka. Zero retuszu skóry.*", "",
      "| Strona | Nr | Miejsce | Plik | Alt | Format | Stan |", "|---|---|---|---|---|---|---|"]
for nazwa, nr, miejsce, pliki, alt, fmt, stan in wiersze:
    lg.append(f"| {nazwa} | {nr} | {miejsce} | {pliki} | {alt or '—'} | {fmt} | {stan} |")
lg += ["", f"Razem zdjęć: {len(wiersze)}.", "", "## Obrazy do udostępniania i znak", "",
       "| Plik | Gdzie | Alt | Format | Stan |", "|---|---|---|---|---|"]
og_miejsca = {}
for n, d in strony.items():
    og = d["seo"]["obraz_og"]
    if og.get("plik"):
        og_miejsca.setdefault(og["plik"], {"alt": og.get("alt", ""), "strony": []})["strony"].append(d["strona"]["nazwa"])
for plik, gdz in og_miejsca.items():
    lg.append(f"| {plik.rsplit('/', 1)[-1]} | {', '.join(gdz['strony'])} | {gdz['alt']} | JPG · 1200 × 630 | {'gotowe' if jest(plik) else 'do przygotowania'} |")
logo = ust["marka"]["logo"]
lg.append(f"| {logo['plik'].rsplit('/', 1)[-1]} | belka górna każdej strony | {logo['alt']} | SVG | {'gotowe' if jest(logo['plik']) else 'do przygotowania'} |")
for plik_, gdzie_, fmt_ in (("/images/marka/arthur-logo.png", "miejsca, w których SVG nie działa (np. e-mail)", "PNG · 1025 × 380"),
                            ("/favicon.ico", "karta przeglądarki", "ICO · 16, 32 i 48 px"),
                            ("/apple-touch-icon.png", "ikona na ekranie telefonu Apple", "PNG · 180 × 180"),
                            ("/images/marka/arthur-ikona-192.png", "ikona aplikacji (manifest)", "PNG · 192 × 192"),
                            ("/images/marka/arthur-ikona-512.png", "ikona aplikacji (manifest)", "PNG · 512 × 512")):
    lg.append(f"| {plik_.rsplit('/', 1)[-1]} | {gdzie_} | — | {fmt_} | {'gotowe' if jest(plik_) else 'do przygotowania'} |")
(ROOT / "docs" / "lista-grafik.md").write_text("\n".join(lg) + "\n", encoding="utf-8")

print("Podglądy:", len(strony), "· JSON-LD:", len(list(out_j.glob('*.json'))),
      "· llms-full.txt pomija strony z zaślepkami:", ", ".join(pominiete) or "—")
