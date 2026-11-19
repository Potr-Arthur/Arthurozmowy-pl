// Ustawienia witryny dla szablonów (19.11.2026). Nazwa strony stoi w jednym miejscu: na stronie (strona.nazwa).
// Lista stron w Ustawieniach (nawigacja.strony) daje tylko kolejność menu i stopki; nazwy dopisujemy tu z plików stron.
import { getCollection, getEntry } from 'astro:content';

/** Jednoliterowe słowa (a, i, o, u, w, z) z twardą spacją, żeby nie zostawały na końcu wiersza. */
export const bezSierot = (tx?: string | null) => (tx ?? '').replace(/(^|\s)([aiouwzAIOUWZ])\s+/g, '$1$2\u00a0');

export async function ustawienia() {
  const ust = (await getEntry('ustawienia', 'witryna'))!.data;
  const nazwy = new Map((await getCollection('strony')).map((w) => [w.data.seo.adres, bezSierot(w.data.strona.nazwa)]));
  const strony = ust.nawigacja.strony.map((l: any) => ({ ...l, tekst: nazwy.get(l.adres) ?? l.tekst ?? l.adres }));
  return { ...ust, nawigacja: { ...ust.nawigacja, strony } };
}
