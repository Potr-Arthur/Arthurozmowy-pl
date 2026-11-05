// Formatowanie tekstów z plików treści: akapity (pusta linia), **pogrubienie**, znacznik {firma},
// zaślepki w nawiasach kwadratowych (widoczne jako „do uzupełnienia” tylko na adresie tymczasowym).

export type Firma = {
  nazwa: string; ulica: string; kod_pocztowy: string; miejscowosc: string; nip: string;
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
  let t = s.replace(/\s*\n\s*/g, ' ').trim();
  if (firma) t = t.replace(/\{firma\}/g, firmaLinia(firma));
  t = esc(t);
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[\s(„])\*(?!\s)([^*]+?)\*(?=[\s.,;:!?)”]|$)/g, '$1<em>$2</em>');
  t = t.replace(/\[([^\]]+)\]/g, '<span class="uzup">[$1]</span>');
  return t;
}

/** Tekst wieloakapitowy → lista akapitów HTML. */
export function akapity(s: string | undefined | null, firma?: Firma): string[] {
  if (!s || !s.trim()) return [];
  return s.split(/\n\s*\n/).map((a) => inline(a, firma)).filter(Boolean);
}

/** H1 z wyróżnionym fragmentem (kursywa w kolorze akcentu). */
export function h1Html(h1: string, wyr?: string): string {
  const h = inline(h1);
  if (!wyr || !wyr.trim()) return h;
  const w = inline(wyr);
  const i = h.indexOf(w);
  return i < 0 ? h : h.slice(0, i) + '<em>' + w + '</em>' + h.slice(i + w.length);
}

const MIESIACE = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia',
  'września', 'października', 'listopada', 'grudnia'];
export function dataPl(d: Date): string {
  return `${d.getUTCDate()} ${MIESIACE[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}
export function dataIso(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** Klasa tonu sekcji: 't2' → 'ton-2'. */
export function tonKlasa(ton: string): string {
  return 'ton-' + ton.replace('t', '');
}
export function tonNr(ton: string): string {
  return ton.replace('t', '');
}

/** Strony, które jeszcze nie istnieją: link pokazujemy jako nieaktywny. */
export const NIEISTNIEJACE = ['/umow'];
export function zewnetrzny(adres: string): boolean {
  return /^https?:\/\//.test(adres);
}
