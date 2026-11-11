// Wymiary zdjęcia do atrybutów width i height (układ nie skacze przy ładowaniu).
// Czyta nagłówek pliku WebP z katalogu public/; gdy się nie da, bierze format z nazwy pliku.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const pamiec = new Map<string, { w: number; h: number }>();

function zNazwy(plik: string): { w: number; h: number } {
  if (/-1x1\./.test(plik)) return { w: 1200, h: 1200 };
  if (/-21x9\./.test(plik)) return { w: 2100, h: 900 };
  return { w: 1200, h: 900 };
}

function zWebp(b: Buffer): { w: number; h: number } | null {
  if (b.length < 30 || b.toString('ascii', 0, 4) !== 'RIFF' || b.toString('ascii', 8, 12) !== 'WEBP') return null;
  const rodzaj = b.toString('ascii', 12, 16);
  if (rodzaj === 'VP8X') return { w: 1 + b.readUIntLE(24, 3), h: 1 + b.readUIntLE(27, 3) };
  if (rodzaj === 'VP8 ') return { w: b.readUInt16LE(26) & 0x3fff, h: b.readUInt16LE(28) & 0x3fff };
  if (rodzaj === 'VP8L') {
    const [b0, b1, b2, b3] = [b[21], b[22], b[23], b[24]];
    return { w: 1 + (((b1 & 0x3f) << 8) | b0), h: 1 + (((b3 & 0xf) << 10) | (b2 << 2) | ((b1 & 0xc0) >> 6)) };
  }
  return null;
}

export function wymiary(plik: string): { w: number; h: number } {
  if (pamiec.has(plik)) return pamiec.get(plik)!;
  let wynik = zNazwy(plik);
  try {
    const odczyt = zWebp(readFileSync(join(process.cwd(), 'public', plik)));
    if (odczyt) wynik = odczyt;
  } catch {
    /* brak pliku: zostaje format z nazwy (skrypt sprawdzający zgłasza brak pliku) */
  }
  pamiec.set(plik, wynik);
  return wynik;
}
