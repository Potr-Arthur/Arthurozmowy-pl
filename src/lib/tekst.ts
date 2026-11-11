// Formatowanie tekstów z plików treści: akapity (pusta linia), **pogrubienie**, linki [tekst](/adres),
// znaczniki {firma}, {email}, {telefon}, {godziny} (dane z Ustawień → Dane firmy),
// zaślepki w nawiasach kwadratowych (widoczne jako „do uzupełnienia” tylko na adresie tymczasowym).

export type Firma = {
  nazwa: string; ulica: string; kod_pocztowy: string; miejscowosc: string; nip: string;
  email?: string; telefon?: string; telefon_godziny?: string;
};

export function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function firmaLinia(f: Firma): string {
  return `${f.nazwa}, ${f.ulica}, ${f.kod_pocztowy} ${f.miejscowosc}, NIP ${f.nip}`;
}

/** Jeden wiersz tekstu → HTML (bez znacznika <p>). */
export function inline(s: string | undefined | null, firma?: Firma): string {
  if (!s) return '';
  let t = esc(s.replace(/\s*\n\s*/g, ' ').trim());
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[\s(„])\*(?!\s)([^*]+?)\*(?=[\s.,;:!?)”]|$)/g, '$1<em>$2</em>');
  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
  t = t.replace(/\[([^\]]+)\](?!\()/g, '<span class="uzup">[$1]</span>');
  if (firma) {
    t = t.replace(/\{firma\}/g, esc(firmaLinia(firma)));
    if (firma.email) t = t.replace(/\{email\}/g, `<a href="mailto:${esc(firma.email)}">${esc(firma.email)}</a>`);
    if (firma.telefon) t = t.replace(/\{telefon\}/g, `<span class="bez-lamania">${esc(firma.telefon)}</span>`);
    if (firma.telefon_godziny) t = t.replace(/\{godziny\}/g, esc(firma.telefon_godziny));
  }
  return t;
}

/** Tekst wieloakapitowy → lista akapitów HTML. */
export function akapity(s: string | undefined | null, firma?: Firma): string[] {
  if (!s || !s.trim()) return [];
  return s.split(/\n\s*\n/).map((a) => inline(a, firma)).filter(Boolean);
}

/** Klasa tonu sekcji: 't2' → 'ton-2'. */
export function tonKlasa(ton: string): string {
  return 'ton-' + ton.replace('t', '');
}
export function tonNr(ton: string): string {
  return ton.replace('t', '');
}

/** Strony, których jeszcze nie ma (zamówienie): link i przycisk pokazujemy jako nieaktywne. */
export const NIEISTNIEJACE = ['/umow'];
export function zewnetrzny(adres: string): boolean {
  return /^https?:\/\//.test(adres);
}
/** Czy adres prowadzi do istniejącej strony witryny (linki zewnętrzne, np. panel klienta, jeszcze nie działają). */
export function dziala(adres?: string): boolean {
  if (!adres) return false;
  if (zewnetrzny(adres)) return false;
  return !NIEISTNIEJACE.includes(adres.split('#')[0]);
}
/** Ścieżka bez kotwicy, '/' dla strony głównej. */
export function sciezka(adres: string): string {
  return adres.split('#')[0] || '/';
}
