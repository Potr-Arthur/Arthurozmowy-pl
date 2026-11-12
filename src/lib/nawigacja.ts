// Rozdziały strony do menu: wejście, jeśli ma etykietę, i rozdziały z etykietą, w kolejności z pliku treści.
// Nazwy biorą się wyłącznie z treści (etykieta rozdziału); szablon niczego nie przemianowuje.
export type Rozdzial = { kotwica: string; etykieta: string };

export function rozdzialyStrony(dane: any): Rozdzial[] {
  const lista: Rozdzial[] = [];
  const w = dane?.wejscie;
  if (w?.etykieta && w?.kotwica) lista.push({ kotwica: w.kotwica, etykieta: w.etykieta });
  for (const s of dane?.sekcje ?? []) if (s.etykieta && s.kotwica) lista.push({ kotwica: s.kotwica, etykieta: s.etykieta });
  return lista;
}
