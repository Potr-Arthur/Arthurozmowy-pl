// To, czego bloki potrzebują poza własnymi polami: Ustawienia, baza pytań i adres oglądanej strony.
export type Kontekst = {
  ust: any;
  baza: Map<string, any>;
  adres: string;
};
