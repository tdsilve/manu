// Exemplos reais, com trechos copiados do manual Electrolux de refrigeradores
// (G0045837, api/data/manuals.yaml). A página é a do PDF.

export type Example = {
  id: string;
  tab: string;
  question: string;
  answer: string;
  section: string;
  page: number;
  excerpt: string;
};

export const MANUAL = {
  brand: "Electrolux",
  title: "Refrigeradores",
  models: "DB44 · IB45 · IF43 · TF38 · TF44 · TF71",
};

export const EXAMPLES: Example[] = [
  {
    id: "lateral",
    tab: "Lateral quente",
    question: "A lateral da geladeira está quente. É defeito?",
    answer: "Não. O fluido refrigerante circula por ali para estabilizar a temperatura interna.",
    section: "5. Limpeza e Manutenção",
    page: 5,
    excerpt:
      "é normal o aquecimento nas regiões próximas às portas e laterais do refrigerador. Isso não causa dano ao funcionamento do produto.",
  },
  {
    id: "limpeza",
    tab: "Limpeza",
    question: "Com o que eu limpo a geladeira por dentro?",
    answer: "Pano úmido com água e bicarbonato: uma colher de sopa para cada litro.",
    section: "5. Limpeza e Manutenção",
    page: 5,
    excerpt:
      "Use somente pano umedecido em uma solução de água e bicarbonato de sódio (dilua 1 colher de sopa de bicarbonato em 1L de água).",
  },
  {
    id: "garantia",
    tab: "Garantia",
    question: "Quanto tempo dura a garantia?",
    answer: "12 meses a partir da nota fiscal: 90 dias de garantia legal e 9 meses de contratual.",
    section: "6. Certificado de Garantia",
    page: 5,
    excerpt:
      "O prazo de vigência da garantia é de 12 (doze) meses contados a partir da data da emissão da nota fiscal",
  },
  {
    id: "nivelar",
    tab: "Nivelamento",
    question: "A porta não fecha sozinha. Como nivelo a geladeira?",
    answer: "Comece pelo pé esquerdo, depois o direito. A única inclinação permitida é para trás.",
    section: "2. Instalação",
    page: 4,
    excerpt:
      "A única inclinação permitida é para trás, facilitando o fechamento das portas.",
  },
];
