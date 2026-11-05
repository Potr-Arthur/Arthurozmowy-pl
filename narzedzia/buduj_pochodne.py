#!/usr/bin/env python3
"""Buduje pliki pochodne z treści arthurozmowy.pl.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/buduj_pochodne.py
Powstają:
  docs/podglad/<strona>.md   tekst strony tak, jak ją zobaczy czytelniczka, z nazwą pola CMS przy każdym elemencie
  docs/mapa-pol.md           mapa: strona → sekcja → blok Matrycy → pola w CMS
  docs/jsonld/<strona>.json  wzór danych strukturalnych, z którego szablon Astro ma budować <script type="application/ld+json">
  public/llms.txt            streszczenie witryny dla modeli AI (llmstxt.org)
  public/llms-full.txt       pełne teksty widocznych stron bez zaślepek
  docs/lista-grafik.md       pliki graficzne do przygotowania: nazwa, alt, format, miejsce, treść zdjęcia
"""
from pathlib import Path
import json, re
import yaml

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "src" / "content"
ust = yaml.safe_load((C / "ustawienia/witryna.yml").read_text(encoding="utf-8"))
baza = {q["id"]: q for q in yaml.safe_load((C / "pytania/baza.yml").read_text(encoding="utf-8"))["pytania"]}
KOLEJNOSC = ["strona-glowna", "jak-to-dziala", "czego-nie-obiecujemy", "pytania", "jak-skorzystac",
             "jak-rozmawiac-z-mama", "o-nas", "kontakt", "404"]
strony = {n: yaml.safe_load((C / "strony" / f"{n}.yml").read_text(encoding="utf-8")) for n in KOLEJNOSC}

DOM = ust["marka"]["domena"].rstrip("/")
F = ust["firma"]
FIRMA = f"{F['nazwa']}, {F['ulica']}, {F['kod_pocztowy']} {F['miejscowosc']}, NIP {F['nip']}"
W = ust["wezwania"]

def rozwin(tx):
    return (tx or "").replace("{firma}", FIRMA)

def czysty(tx):
    """Markdown → zwykły tekst (do JSON-LD i llms-full.txt)."""
    tx = rozwin(tx)
    tx = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tx)
    tx = tx.replace("**", "")
    return re.sub(r"\n{2,}", "\n\n", tx).strip()

ZASLEPKA = re.compile(r"\[(?!\s*\])[^\]]+\](?!\()")

BLOKI = {"rozdzial": "3 · rozdział", "zasady": "6 · lista zasad", "krok": "9 · krok z przykładem",
         "watpliwosci": "10 · wątpliwości", "pytania": "8 · pytanie i odpowiedź",
         "faq": "19 · FAQ w akordeonie", "kontakt": "14 · dane i kontakt", "koniec": "12 · pas wezwań"}

# ------------------------------------------------ podgląd strony

def wezwania_md(w, pref):
    out = []
    if not w:
        return out
    if w.get("glowne"):
        out.append(f"- **Przycisk (okienko „{ust['okno_rozmowy']['tytul']}”):** {W['glowne']['przycisk']}  `{pref}.glowne`")
    if w.get("dopisek"):
        out.append(f"- **Pod przyciskiem:** {W['glowne']['dopisek']}  `{pref}.dopisek`")
    if w.get("jawnosc"):
        out.append(f"- **Jawność:** {W['jawnosc']}  `{pref}.jawnosc`")
    if w.get("zakupowe"):
        if w.get("nad_zakupowym"):
            out.append(f"- **Nad przyciskiem:** {W['zakupowe']['nad_przyciskiem']}  `{pref}.nad_zakupowym`")
        out.append(f"- **Przycisk zakupowy:** {W['zakupowe']['przycisk']} → {W['zakupowe']['adres']}  `{pref}.zakupowe`")
    return out

def zdjecie_md(z, pref):
    if not z:
        return []
    if not z.get("widoczne"):
        return [f"- *Miejsce na zdjęcie ukryte, kadr: {z.get('kadr', '')}*  `{pref}`"]
    return [f"- **Zdjęcie:** `{z['plik_desktop']}` · `{z['plik_telefon']}`  `{pref}`",
            f"- **Alt:** {z['alt']}  `{pref}.alt`"]

def linki_md(ls, pref):
    out = []
    for i, l in enumerate(ls or []):
        stan = "" if l.get("aktywny", True) else " *(nieaktywny)*"
        out.append(f"- **Link:** {l['tekst']} → {l.get('adres') or '—'}{stan}  `{pref}[{i}]`")
    return out

def cennik_md(c, pref):
    if not c or not c.get("widoczny"):
        return []
    out = []
    for p in ust["pakiety"]["lista"]:
        nazwa = f"**{p['nazwa'][:1].upper()}{p['nazwa'][1:]}** " if c.get("pokaz_nazwy") and p.get("nazwa") else ""
        out.append(f"- {nazwa}{p['cena']} zł: {p['opis']}")
    out.append(f"\n*Cennik z Ustawień → Pakiety*  `{pref}`")
    return out

def pytanie_md(pid, poziom="###"):
    q = baza[pid]
    out = [f"{poziom} {q['pytanie']}  `baza:{pid}`", "", rozwin(q["odpowiedz"])]
    if q.get("link"):
        out += ["", f"**Link:** {q['link']['tekst']} → {q['link']['adres']}"]
    return out

def podglad(n, d):
    seo, w = d["seo"], d["wejscie"]
    o = [f"# {d['strona']['nazwa']} · {seo['adres']}", "",
         f"*Plik: `src/content/strony/{n}.yml` · szablon: {d['strona']['szablon']} · "
         f"aktualizacja: {seo['zaktualizowano']} · autor: {seo['autor']}*", "",
         "## Wyszukiwarki i AI", "",
         f"- **Tytuł ({len(seo['tytul'])} zn.):** {seo['tytul']}  `seo.tytul`",
         f"- **Opis ({len(seo['opis'])} zn.):** {seo['opis']}  `seo.opis`",
         f"- **Obraz do udostępniania:** `{seo['obraz_og']['plik'] or '—'}` · alt: {seo['obraz_og']['alt'] or '—'}  `seo.obraz_og`",
         f"- **Dane strukturalne:** {', '.join(seo['schemat']) or '—'}  `seo.schemat`",
         f"- **W wyszukiwarkach:** {'tak' if seo['indeksuj'] else 'nie (noindex)'}  `seo.indeksuj`",
         f"- **Streszczenie dla AI:** {d['geo']['streszczenie'] or '—'}  `geo.streszczenie`", ""]
    blok = "1 · wejście strony głównej" if d["strona"]["szablon"] == "glowna" else (
        "404 · strona błędu" if d["strona"]["szablon"] == "blad" else "2 · Hero2")
    o += [f"## Wejście · blok {blok}" + (f" · #{w['kotwica']} · spis treści: „{w['etykieta']}”" if w.get("kotwica") else ""), ""]
    o += zdjecie_md(w.get("zdjecie"), "wejscie.zdjecie")
    o += [f"- **H1:** {w['h1']}  `wejscie.h1`"]
    if w.get("h1_wyroznienie"):
        o += [f"- **Wyróżnione w H1:** {w['h1_wyroznienie']}  `wejscie.h1_wyroznienie`"]
    o += ["", "**Wstęp** `wejscie.lid`", "", rozwin(w["lid"]), ""]
    if w.get("przycisk_powrotu"):
        o += [f"- **Przycisk:** {w['przycisk_powrotu']['tekst']} → {w['przycisk_powrotu']['adres']}  `wejscie.przycisk_powrotu`"]
    o += linki_md(w.get("linki"), "wejscie.linki")
    o += wezwania_md(w.get("wezwania"), "wejscie.wezwania")
    if w.get("pokaz_autora_i_date"):
        o += [f"- **Autor i data (blok 18):** {seo['autor']} · {seo['zaktualizowano']}"]
    for i, s in enumerate(d.get("sekcje", [])):
        p = f"sekcje[{i}]"
        typ = s["typ"]
        nag = f"## {i + 1}. {s.get('etykieta') or ('Koniec strony' if typ == 'koniec' else '(bez etykiety)')}"
        nag += f" · blok {BLOKI[typ]} · ton {s.get('ton')}"
        if s.get("kotwica"):
            nag += f" · #{s['kotwica']}"
        o += ["", nag, ""]
        if s.get("numer"):
            o += [f"*Krok {s['numer']}*", ""]
        if s.get("wstep"):
            o += [f"**Wstęp rozdziału (blok 15)** `{p}.wstep`", "", s["wstep"], ""]
        if s.get("h2"):
            o += [f"**H2** `{p}.h2`", "", s["h2"], ""]
        o += zdjecie_md(s.get("zdjecie"), f"{p}.zdjecie")
        if s.get("tekst"):
            o += ["", f"**Tekst** `{p}.tekst`", "", rozwin(s["tekst"]), ""]
        for j, df in enumerate(s.get("definicje") or []):
            o += [f"**{df['termin']}** {df['opis']}  `{p}.definicje[{j}]`", ""]
        if s.get("lista"):
            o += [f"**{s['lista']['wprowadzenie']}** `{p}.lista`", ""] + [f"- {x}" for x in s["lista"]["punkty"]] + [""]
        o += cennik_md(s.get("cennik"), f"{p}.cennik")
        if s.get("tekst_po"):
            o += ["", f"**Tekst pod cennikiem lub listą** `{p}.tekst_po`", "", rozwin(s["tekst_po"]), ""]
        for j, z in enumerate(s.get("zasady") or []):
            o += [f"{j + 1}. **{z['naglowek']}** {z['tekst']}", f"   *Dlaczego:* {z['dlaczego']}  `{p}.zasady[{j}]`"]
        if s.get("przyklad"):
            o += [f"**Przykład:** „{s['przyklad']}”  `{p}.przyklad`", ""]
        for j, pr in enumerate(s.get("pary") or []):
            o += [f"- **„{pr['mama']}”** „{pr['odpowiedz']}”  `{p}.pary[{j}]`"]
        if s.get("zakonczenie"):
            o += ["", f"{s['zakonczenie']}  `{p}.zakonczenie`", ""]
        if typ == "pytania":
            for pid in s["pytania"]:
                o += [""] + pytanie_md(pid, "###")
            o += [""]
        if typ == "faq":
            o += [f"**{s['h2']}** `{p}.h2`", ""]
            for pid in s["pytania"]:
                o += [f"- {baza[pid]['pytanie']}  `baza:{pid}`"]
            o += [""]
        if typ == "kontakt":
            pk = s.get("pokaz") or {}
            if pk.get("email"): o += [f"- E-mail: {F['email']}"]
            if pk.get("telefon"):
                o += [f"- Telefon: {F['telefon']}" + (f" {F['telefon_godziny']}" if pk.get("godziny_telefonu") else "")]
            if pk.get("czas_odpowiedzi"): o += [f"- {F['czas_odpowiedzi']}"]
            if s.get("uwaga"): o += ["", f"{s['uwaga']}  `{p}.uwaga`"]
            o += [""]
        ak = s.get("akapit_ukryty")
        if ak:
            stan = "widoczny" if ak.get("widoczny") else f"ukryty do: {ak.get('warunek')}"
            o += [f"*Akapit {stan}:* {ak['tekst']}  `{p}.akapit_ukryty`", ""]
        og = s.get("okno_glosu")
        if og:
            o += [f"**Okno głosu (blok 17, {og['wariant']}, {'widoczne' if og.get('widoczne') else 'ukryte'})** `{p}.okno_glosu`", "",
                  f"*{og['etykieta']}*"] + [f"> **{x['kto']}:** {x['kwestia']}" for x in og.get("dialog", [])] + \
                 ([f"> {og['zdanie']}"] if og.get("zdanie") else []) + ["", f"*{og.get('przypis', '')}*", ""]
        cz = s.get("cudze_zdanie")
        if cz:
            o += [f"*Cudze zdanie (blok 16): {'widoczne' if cz.get('widoczne') else 'miejsce zarezerwowane, ukryte'}*  `{p}.cudze_zdanie`", ""]
        o += linki_md(s.get("linki"), f"{p}.linki")
        o += wezwania_md(s.get("wezwania"), f"{p}.wezwania")
    return "\n".join(o).rstrip() + "\n"

out_p = ROOT / "docs" / "podglad"
out_p.mkdir(parents=True, exist_ok=True)
for n, d in strony.items():
    (out_p / f"{n}.md").write_text(podglad(n, d), encoding="utf-8")

# ------------------------------------------------ mapa pól

m = ["# Mapa pól: strona → sekcja → blok Matrycy → pole w CMS", "",
     "*Plik generowany przez narzedzia/buduj_pochodne.py. Ścieżka pola odpowiada kluczom w pliku strony i polom w Sveltia CMS.*", ""]
for n, d in strony.items():
    m += [f"## {d['strona']['nazwa']} · `{d['seo']['adres']}` · `src/content/strony/{n}.yml`", "",
          "| Kolejność | Sekcja (spis treści) | Kotwica | Ton | Blok Matrycy | Pola w CMS |", "|---|---|---|---|---|---|"]
    w = d["wejscie"]
    pola = ["seo.*", "geo.streszczenie", "wejscie.h1", "wejscie.lid", "wejscie.zdjecie", "wejscie.wezwania"]
    m += [f"| 0 | {w.get('etykieta') or 'Wejście'} | {('#' + w['kotwica']) if w.get('kotwica') else '—'} | hero | "
          f"{'1' if d['strona']['szablon'] == 'glowna' else ('404' if d['strona']['szablon'] == 'blad' else '2')}"
          f"{', 13' if (w.get('zdjecie') or {}).get('widoczne') else ''}{', 18' if w.get('pokaz_autora_i_date') else ''} | "
          f"{', '.join('`' + x + '`' for x in pola)} |"]
    for i, s in enumerate(d.get("sekcje", [])):
        klucze = [k for k, v in s.items() if k not in ("typ", "kotwica", "etykieta", "ton") and v not in (None, "", [], {})]
        bl = [BLOKI[s["typ"]].split(" ")[0]]
        if s.get("definicje"): bl.append("4")
        if s.get("lista"): bl.append("5")
        if (s.get("cennik") or {}).get("widoczny"): bl.append("7")
        if s.get("linki"): bl.append("11")
        if any((s.get("wezwania") or {}).values()) and s["typ"] != "koniec": bl.append("12")
        if s.get("zdjecie"): bl.append("13")
        if s.get("wstep"): bl.append("15")
        if s.get("cudze_zdanie"): bl.append("16")
        if s.get("okno_glosu"): bl.append("17")
        m += [f"| {i + 1} | {s.get('etykieta') or ('Koniec strony' if s['typ'] == 'koniec' else '—')} | "
              f"{('#' + s['kotwica']) if s.get('kotwica') else '—'} | {s.get('ton')} | {', '.join(bl)} | "
              f"`sekcje[{i}]` typ `{s['typ']}`: {', '.join('`' + k + '`' for k in klucze)} |"]
    m += [""]
m += ["## Ustawienia wspólne · `src/content/ustawienia/witryna.yml`", "",
      "| Grupa | Co zawiera | Gdzie się pokazuje |", "|---|---|---|",
      "| `marka` | nazwa, domena, definicja, logo | nagłówek, JSON-LD, llms.txt, odpowiedź „Czym są arthurozmowy?” |",
      "| `naglowek` | napisy menu („Menu”, „Na tej stronie”, „Strony”), link „Panel klienta”, przycisk przyklejony na telefonie | nagłówek każdej strony |",
      "| `nawigacja` | jedna lista stron z nazwami i adresami | menu w nagłówku i stopka |",
      "| `wezwania` | teksty wezwania głównego, jawności i zakupowego | tam, gdzie strona włączy dane wezwanie; zakup także w menu i stopce |",
      "| `okno_rozmowy` | tytuł, wstęp, pola, wybór „teraz” albo termin, przycisk, komunikaty, zgoda | okienko otwierane przyciskiem „Porozmawiaj z Arthurem” |",
      "| `pakiety` | ceny, liczby rozmów, opisy | cennik (blok 7), JSON-LD Offer, llms.txt |",
      "| `firma` | dane firmy i kontaktowe | sekcje kontaktu, znacznik {firma}, stopka, JSON-LD |",
      "| `stopka` | linki prawne, kontakt, jawność, statystyki, prawa (strony z `nawigacja`) | stopka każdej strony |", "",
      "## Baza pytań · `src/content/pytania/baza.yml`", "",
      "| Identyfikator | Pytanie | Rozdział na stronie Pytania | Akordeony na podstronach |", "|---|---|---|---|"]
uzycie = {}
for n, d in strony.items():
    for s in d.get("sekcje", []):
        if s["typ"] == "faq":
            for pid in s["pytania"]:
                uzycie.setdefault(pid, []).append(d["strona"]["nazwa"])
rozdzial = {pid: s["etykieta"] for s in strony["pytania"]["sekcje"] if s["typ"] == "pytania" for pid in s["pytania"]}
for pid, q in baza.items():
    m += [f"| `{pid}` | {q['pytanie']} | {rozdzial.get(pid, '—')} | {', '.join(uzycie.get(pid, [])) or '—'} |"]
(ROOT / "docs" / "mapa-pol.md").write_text("\n".join(m) + "\n", encoding="utf-8")

# ------------------------------------------------ JSON-LD

ORG_ID, WEB_ID, USL_ID, OS_ID = f"{DOM}/#organizacja", f"{DOM}/#witryna", f"{DOM}/#usluga", f"{DOM}/o-nas#piotr-jaworski"
nip = re.sub(r"\D", "", F["nip"])
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
oferty = [{"@type": "Offer", "name": (f"{p['nazwa'][:1].upper()}{p['nazwa'][1:]}: " if p["nazwa"] else "") + f"{p['cena']} zł miesięcznie, {p['opis']}",
           "price": str(p["cena"]), "priceCurrency": ust["pakiety"]["waluta"],
           "priceSpecification": {"@type": "UnitPriceSpecification", "price": p["cena"],
                                  "priceCurrency": ust["pakiety"]["waluta"], "unitCode": "MON",
                                  "valueAddedTaxIncluded": True},
           "url": DOM + "/jak-skorzystac#pakiety-i-platnosci", "seller": {"@id": ORG_ID}}
          for p in ust["pakiety"]["lista"]]
usluga = {"@type": "Service", "@id": USL_ID, "name": ust["marka"]["nazwa"], "serviceType": "Rozmowy telefoniczne z programem AI",
          "description": ust["marka"]["definicja"], "provider": {"@id": ORG_ID}, "areaServed": "PL",
          "availableLanguage": "pl", "offers": oferty}
osoba = {"@type": "Person", "@id": OS_ID, "name": ust["autor"]["imie_nazwisko"], "url": DOM + "/o-nas",
         "worksFor": {"@id": ORG_ID}}

def strona_ld(n, d, typ="WebPage"):
    seo = d["seo"]
    return {"@type": typ, "@id": DOM + seo["adres"] + "#strona", "url": DOM + seo["adres"], "name": seo["tytul"],
            "description": seo["opis"], "inLanguage": ust["marka"]["jezyk"], "isPartOf": {"@id": WEB_ID},
            "about": {"@id": USL_ID}, "dateModified": str(seo["zaktualizowano"]), "author": {"@id": OS_ID},
            **({"primaryImageOfPage": DOM + seo["obraz_og"]["plik"]} if seo["obraz_og"]["plik"] else {})}

def okruszki(d):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Strona główna", "item": DOM + "/"},
        {"@type": "ListItem", "position": 2, "name": d["strona"]["nazwa"], "item": DOM + d["seo"]["adres"]}]}

out_j = ROOT / "docs" / "jsonld"
out_j.mkdir(parents=True, exist_ok=True)
for n, d in strony.items():
    sch = set(d["seo"]["schemat"])
    graf = []
    if not d["seo"]["indeksuj"]:
        continue
    typ_strony = "AboutPage" if "AboutPage" in sch else "ContactPage" if "ContactPage" in sch else \
        "FAQPage" if "FAQPage" in sch else "WebPage"
    if typ_strony == "FAQPage":
        faq = strona_ld(n, d, "FAQPage")
        faq["mainEntity"] = [{"@type": "Question", "name": baza[pid]["pytanie"],
                              "acceptedAnswer": {"@type": "Answer", "text": czysty(baza[pid]["odpowiedz"])}}
                             for s in d["sekcje"] if s["typ"] == "pytania" for pid in s["pytania"]]
        graf.append(faq)
    else:
        graf.append(strona_ld(n, d, typ_strony))
    if "Organization" in sch: graf.append(org)
    if "WebSite" in sch: graf.append(witryna)
    if "Service" in sch or "Offer" in sch: graf.append(usluga)
    if "Person" in sch: graf.append(osoba)
    if "HowTo" in sch:
        kroki = [s for s in d["sekcje"] if s["typ"] == "krok"]
        graf.append({"@type": "HowTo", "name": d["wejscie"]["h1"], "description": czysty(d["wejscie"]["lid"]),
                     "inLanguage": ust["marka"]["jezyk"],
                     "step": [{"@type": "HowToStep", "position": s["numer"], "name": s["h2"],
                               "text": czysty(s["tekst"]), "url": DOM + d["seo"]["adres"] + "#" + s["kotwica"]}
                              for s in kroki]})
    if "BreadcrumbList" in sch: graf.append(okruszki(d))
    (out_j / f"{n}.json").write_text(json.dumps({"@context": "https://schema.org", "@graph": graf},
                                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ------------------------------------------------ llms.txt i llms-full.txt

g = strony["strona-glowna"]
l = [f"# {ust['marka']['nazwa']}", "", f"> {ust['marka']['definicja']}", "",
     g["geo"]["streszczenie"], "",
     "Najważniejsze fakty:", "",
     f"- Usługę świadczy firma {FIRMA}.",
     "- Usługę zamawia i opłaca dorosłe dziecko, a z Arthurem rozmawia jego mama, tylko za swoją zgodą.",
     "- Arthur jest programem opartym na sztucznej inteligencji i nigdy nie udaje człowieka; „h” w imieniu to „h” jak humanoid.",
     "- Pakiety: " + "; ".join((f"{p['nazwa']} " if p["nazwa"] else "") + f"{p['cena']} zł miesięcznie z VAT: {p['opis']}" for p in ust["pakiety"]["lista"]) + ".",
     "- Pierwszy, próbny miesiąc jest bezpłatny. Rezygnacja jednym kliknięciem uruchamia 15-dniowe „Pożegnanie”.",
     "- Granice: Arthur nie zastępuje pomocy w domu, przycisku SOS ani lekarza, nie wykrywa upadku między rozmowami, "
     "nie diagnozuje i nie obiecuje ochrony przed demencją.", "",
     "## Strony", ""]
for n in KOLEJNOSC[1:]:
    d = strony[n]
    if not d["seo"]["indeksuj"]:
        continue
    l.append(f"- [{d['strona']['nazwa']}]({DOM}{d['seo']['adres']}): {d['geo']['streszczenie']}")
l += ["", "## Pełne teksty", "", f"- [Wszystkie teksty witryny w jednym pliku]({DOM}/llms-full.txt)", ""]
(ROOT / "public" / "llms.txt").write_text("\n".join(l), encoding="utf-8")

pelne = [f"# {ust['marka']['nazwa']} · pełne teksty witryny", "", f"> {ust['marka']['definicja']}", ""]
pominiete = []
for n in KOLEJNOSC:
    d = strony[n]
    if not d["seo"]["indeksuj"]:
        continue
    blok = [f"## {d['seo']['tytul']}", f"{DOM}{d['seo']['adres']}", "", czysty(d["wejscie"]["h1"]), "", czysty(d["wejscie"]["lid"])]
    for s in d.get("sekcje", []):
        if s["typ"] in ("koniec",):
            continue
        if s.get("h2") and s["typ"] != "faq": blok += ["", "### " + czysty(s["h2"])]
        if s.get("wstep"): blok += ["", czysty(s["wstep"])]
        if s.get("tekst"): blok += ["", czysty(s["tekst"])]
        for df in s.get("definicje") or []: blok += ["", f"{df['termin']} {df['opis']}"]
        if s.get("lista"): blok += ["", s["lista"]["wprowadzenie"] + ":"] + [f"- {x}" for x in s["lista"]["punkty"]]
        if (s.get("cennik") or {}).get("widoczny"):
            blok += [""] + [f"- " + (f"{p['nazwa'][:1].upper()}{p['nazwa'][1:]} " if (s.get("cennik") or {}).get("pokaz_nazwy") and p["nazwa"] else "") + f"{p['cena']} zł: {p['opis']}" for p in ust["pakiety"]["lista"]]
        if s.get("tekst_po"): blok += ["", czysty(s["tekst_po"])]
        for z in s.get("zasady") or []: blok += ["", f"{z['naglowek']} {z['tekst']} Dlaczego: {z['dlaczego']}"]
        if s.get("przyklad"): blok += ["", f"Przykład: „{s['przyklad']}”"]
        for pr in s.get("pary") or []: blok += [f"- „{pr['mama']}” – „{pr['odpowiedz']}”"]
        if s.get("zakonczenie"): blok += ["", s["zakonczenie"]]
        if s["typ"] == "pytania":
            for pid in s["pytania"]:
                blok += ["", "### " + baza[pid]["pytanie"], "", czysty(baza[pid]["odpowiedz"])]
    tekst = "\n".join(blok)
    if ZASLEPKA.search(tekst):
        pominiete.append(n)
        continue
    pelne += [tekst, ""]
(ROOT / "public" / "llms-full.txt").write_text("\n".join(pelne), encoding="utf-8")

# ------------------------------------------------ lista grafik

# Zasada z 5.11.2026: strona główna ma 4 zdjęcia (wejście + 3), każda podstrona 2 (wejście + 1), strona 404 żadnego.
# Nowa treść zdjęcia = nowa nazwa pliku; nazwy nigdy nie wracają do innej treści.
# Stan zdjęcia wynika z plików w public/images: oba pliki (-desk i -tel) na miejscu to „gotowe”.
PUB = ROOT / "public"
def jest(sciezka):
    return bool(sciezka) and (PUB / sciezka.lstrip("/")).is_file()
TRESC_OG = {"arthurozmowy-og-glowna": "Rozmowa przy stole: mama z ożywieniem opowiada rozmówczyni widocznej od tyłu",
            "arthurozmowy-og-mama-portret-usmiech": "Portret mamy z lekkim uśmiechem, w błękitnej jedwabnej bluzce (jeden obraz dla 6 podstron)",
            "arthurozmowy-og-o-nas": "Mama z profilu z uwagą patrzy w bok, poza kadr"}
FMT_HERO = "21:9 · 2100 × 900 (desk) / 4:3 · 1200 × 900 (tel)"
FMT = "3:4 · 900 × 1200 (desk) / 4:3 · 1200 × 900 (tel)"

def prompt_z_kadru(kadr):
    m = re.search(r"prompt ([A-Z])\b", kadr or "")
    return m.group(1) if m else ""

wiersze = []
for n, d in strony.items():
    nazwa = d["strona"]["nazwa"]
    miejsca = [("wejście", d["wejscie"].get("zdjecie") or {}, d["strona"]["szablon"] == "glowna")]
    miejsca += [(s_.get("etykieta") or s_.get("kotwica"), s_.get("zdjecie") or {}, False) for s_ in d.get("sekcje", [])]
    nr = 0
    for miejsce, z, hero in miejsca:
        if not z.get("plik_desktop"):
            continue
        nr += 1
        plik = z["plik_desktop"].rsplit("/", 1)[-1].replace("-desk.webp", "")
        if jest(z.get("plik_desktop")) and jest(z.get("plik_telefon")):
            stan = "gotowe" + ("" if z.get("widoczne") else ", na stronie ukryte")
        else:
            pr = prompt_z_kadru(z.get("kadr"))
            stan = "do zrobienia" + (f", prompt {pr}" if pr else "")
        wiersze.append((nazwa, nr, miejsce, plik, z.get("alt", ""), FMT_HERO if hero else FMT, stan, z.get("kadr", "")))

lg = ["# Zdjęcia witryny arthurozmowy.pl", "",
      "*Plik generowany przez narzedzia/buduj_pochodne.py z plików stron. Zasada: strona główna ma 4 zdjęcia (wejście i 3 w rozdziałach), "
      "każda podstrona 2 (wejście i 1 w rozdziale), strona 404 żadnego. Nowa treść zdjęcia dostaje nową nazwę pliku. "
      "Każde zdjęcie to dwa pliki o tej samej treści: `-desk.webp` i `-tel.webp` w `public/images/strony/`. "
      "Alt: co naprawdę widać, słowami strony, nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka. Zero retuszu skóry.*", "",
      "| Strona | Nr | Miejsce | Plik | Alt | Format | Stan |", "|---|---|---|---|---|---|---|"]
for nazwa, nr, miejsce, plik, alt, fmt, stan, _ in wiersze:
    lg.append(f"| {nazwa} | {nr} | {miejsce} | {plik} | {alt or '—'} | {fmt} | {stan} |")
lg += ["", f"Razem zdjęć: {len(wiersze)}.", "", "## Obrazy do udostępniania i znak", "",
       "| Plik | Gdzie | Alt | Format | Stan |", "|---|---|---|---|---|"]
og_miejsca = {}
for n, d in strony.items():
    og = d["seo"]["obraz_og"]
    if og.get("plik"):
        b_ = og["plik"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        og_miejsca.setdefault(b_, {"alt": og.get("alt", ""), "strony": []})["strony"].append(d["strona"]["nazwa"])
for b_, g in og_miejsca.items():
    stan = "gotowe" if jest(f"/images/og/{b_}.jpg") else "do przygotowania"
    lg.append(f"| {b_}.jpg | {', '.join(g['strony'])} | {g['alt']} | JPG · 1200 × 630 · {TRESC_OG.get(b_, '')} | {stan} |")
logo = ust["marka"]["logo"]
lg.append(f"| {logo['plik'].rsplit('/', 1)[-1]} | nagłówek każdej strony | {logo['alt']} | SVG | {'gotowe' if jest(logo['plik']) else 'do przygotowania'} |")
for plik_, gdzie_, fmt_ in (("/images/marka/arthur-logo.png", "miejsca, w których SVG nie działa (np. e-mail)", "PNG · 1025 × 380"),
                            ("/favicon.ico", "karta przeglądarki", "ICO · 16, 32 i 48 px"),
                            ("/apple-touch-icon.png", "ikona na ekranie telefonu Apple", "PNG · 180 × 180"),
                            ("/images/marka/arthur-ikona-192.png", "ikona aplikacji (manifest)", "PNG · 192 × 192"),
                            ("/images/marka/arthur-ikona-512.png", "ikona aplikacji (manifest)", "PNG · 512 × 512")):
    lg.append(f"| {plik_.rsplit('/', 1)[-1]} | {gdzie_} | — | {fmt_} | {'gotowe' if jest(plik_) else 'do przygotowania'} |")
(ROOT / "docs" / "lista-grafik.md").write_text("\n".join(lg) + "\n", encoding="utf-8")

print("Podglądy:", len(strony), "· JSON-LD:", len(list(out_j.glob('*.json'))),
      "· llms-full.txt pomija strony z zaślepkami:", ", ".join(pominiete) or "—")
