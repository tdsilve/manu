import { describe, expect, it } from "vitest";
import { applyFound, decide, productLabel } from "@/lib/detection-flow";
import type { Detection, Product, SelectedProduct } from "@/lib/products";

const electrolux: Product = {
  manual_id: "electrolux-g0045837",
  brand: "Electrolux",
  category: "geladeira",
  model_codes: ["DB44", "IB45"],
};
const brastemp: Product = {
  manual_id: "brastemp-bre57fe",
  brand: "Brastemp",
  category: "geladeira",
  model_codes: ["BRE57FE"],
};

const db44: SelectedProduct = { product: electrolux, code: "DB44" };
const ib45: SelectedProduct = { product: electrolux, code: "IB45" };
const bre: SelectedProduct = { product: brastemp, code: "BRE57FE" };

function detection(overrides: Partial<Detection> = {}): Detection {
  return { matches: [], unrecognized: [], only_codes: false, ...overrides };
}
const found = (p: SelectedProduct) => ({ code: p.code, matched: p.code.toLowerCase(), product: p.product });

describe("productLabel", () => {
  it("mostra código, categoria e marca", () => {
    expect(productLabel(db44)).toBe("DB44 · geladeira Electrolux");
  });
});

describe("applyFound (AC-17)", () => {
  it("sem produto atual, escolhe o achado sem aviso", () => {
    expect(applyFound(null, db44)).toEqual({ product: db44, notice: null });
  });

  it("outro manual troca o produto e avisa com código, categoria e marca", () => {
    const result = applyFound(db44, bre);

    expect(result.product).toBe(bre);
    expect(result.notice).toEqual({ kind: "switched", text: "Troquei para BRE57FE, geladeira Brastemp." });
  });

  it("outro código do mesmo manual atualiza o código em silêncio", () => {
    expect(applyFound(db44, ib45)).toEqual({ product: ib45, notice: null });
  });

  it("o mesmo código do mesmo manual não muda nada nem avisa", () => {
    expect(applyFound(db44, db44)).toEqual({ product: db44, notice: null });
  });
});

describe("decide: nenhum aparelho achado (AC-9, AC-18)", () => {
  it("sem produto e sem nada parecido com código, pergunta sem produto e sem aviso", () => {
    expect(decide(detection(), null)).toEqual({ kind: "ask", product: null, notice: null });
  });

  it("com produto atual, segue com ele (AC-9)", () => {
    expect(decide(detection(), db44)).toEqual({ kind: "ask", product: db44, notice: null });
  });

  it("código desconhecido sem produto avisa que respondeu com todos os manuais (AC-18)", () => {
    const action = decide(detection({ unrecognized: ["XY99"] }), null);

    expect(action).toEqual({
      kind: "ask",
      product: null,
      notice: { kind: "unrecognized", text: "Não reconheci XY99; respondi com todos os manuais." },
    });
  });

  it("código desconhecido com produto avisa que respondeu com o manual do chip (AC-18)", () => {
    const action = decide(detection({ unrecognized: ["XY99", "ZZ1"] }), db44);

    expect(action).toEqual({
      kind: "ask",
      product: db44,
      notice: { kind: "unrecognized", text: "Não reconheci XY99; respondi com o manual de DB44." },
    });
  });
});

describe("decide: um aparelho achado (AC-8, AC-14, AC-17)", () => {
  it("sem produto atual, escolhe e pergunta", () => {
    const action = decide(detection({ matches: [found(db44)] }), null);

    expect(action).toEqual({ kind: "ask", product: db44, notice: null });
  });

  it("só o código (only_codes) escolhe e não pergunta", () => {
    const action = decide(detection({ matches: [found(db44)], only_codes: true }), null);

    expect(action).toEqual({ kind: "select", product: db44, notice: null });
  });

  it("outro manual com chip troca, avisa e pergunta", () => {
    const action = decide(detection({ matches: [found(bre)] }), db44);

    expect(action).toEqual({
      kind: "ask",
      product: bre,
      notice: { kind: "switched", text: "Troquei para BRE57FE, geladeira Brastemp." },
    });
  });

  it("só o código de outro manual troca e avisa, sem perguntar", () => {
    const action = decide(detection({ matches: [found(bre)], only_codes: true }), db44);

    expect(action.kind).toBe("select");
    expect(action).toMatchObject({ product: bre, notice: { kind: "switched" } });
  });

  it("outro código do mesmo manual atualiza o código e pergunta, sem aviso", () => {
    const action = decide(detection({ matches: [found(ib45)] }), db44);

    expect(action).toEqual({ kind: "ask", product: ib45, notice: null });
  });

  it("o mesmo código do chip pergunta com o produto atual", () => {
    const action = decide(detection({ matches: [found(db44)] }), db44);

    expect(action).toEqual({ kind: "ask", product: db44, notice: null });
  });

  it("o código achado vem do registro, e não do trecho escrito na pergunta", () => {
    const action = decide(
      detection({ matches: [{ code: "DB44", matched: "db 44", product: electrolux }] }),
      null,
    );

    expect(action).toMatchObject({ product: { code: "DB44" } });
  });
});

describe("decide: vários aparelhos (AC-16)", () => {
  it("não pergunta e devolve as opções na ordem do texto", () => {
    const action = decide(detection({ matches: [found(bre), found(db44)] }), null);

    expect(action).toEqual({ kind: "choose", options: [bre, db44], onlyCodes: false });
  });

  it("repassa only_codes para a escolha fechar sem resposta", () => {
    const action = decide(detection({ matches: [found(db44), found(bre)], only_codes: true }), db44);

    expect(action).toMatchObject({ kind: "choose", onlyCodes: true });
  });

  it("não troca o produto atual antes de a pessoa escolher", () => {
    const action = decide(detection({ matches: [found(db44), found(bre)] }), ib45);

    expect(action.kind).toBe("choose");
    expect(action).not.toHaveProperty("product");
  });
});
