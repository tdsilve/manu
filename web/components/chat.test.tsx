// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Chat } from "@/components/chat";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
// O mascote é 3D (three.js) e não importa para o comportamento do chat.
vi.mock("@/components/manu", () => ({ Manu: () => <div data-testid="manu" /> }));
vi.mock("@/lib/use-pointer", () => ({ useFinePointer: () => false }));

const electrolux = { manual_id: "electrolux-g0045837", brand: "Electrolux", category: "geladeira", model_codes: ["DB44"] };
const brastemp = { manual_id: "brastemp-bre57fe", brand: "Brastemp", category: "geladeira", model_codes: ["BRE57FE"] };

type Match = { code: string; matched: string; product: typeof electrolux; approximate?: boolean };
const DB44: Match = { code: "DB44", matched: "DB44", product: electrolux };
const BRE: Match = { code: "BRE57FE", matched: "BRE57FE", product: brastemp };

let asked: Record<string, unknown>[];
let detect: (text: string) => object | Promise<object>;
let answer: (body: Record<string, unknown>) => object | Promise<object>;

beforeEach(() => {
  asked = [];
  detect = () => ({ matches: [], unrecognized: [], only_codes: false });
  answer = () => ({ answer: "Resposta do manual.", refused: false, citations: [] });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const body = init?.body ? JSON.parse(String(init.body)) : {};
      if (url.includes("/api/products/detect")) return Response.json(await detect(body.text));
      asked.push(body);
      return Response.json(await answer(body));
    }),
  );
  window.scrollTo = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// O aviso também vai para a região de leitor de tela, então o texto existe duas vezes: confere na barra visível.
const productBar = () => document.querySelector("[data-slot=product-bar]");

async function ask(user: ReturnType<typeof userEvent.setup>, question: string) {
  await user.type(screen.getByRole("textbox", { name: "Sua dúvida" }), `${question}{Enter}`);
}

describe("Nova conversa e logo (feature 5)", () => {
  it("na tela inicial não há botão de nova conversa e aparecem o mascote e os exemplos", () => {
    render(<Chat initialQuestion="" />);

    expect(screen.queryByRole("button", { name: /Nova conversa/ })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Qual é a sua dúvida?" })).toBeInTheDocument();
    expect(screen.getByLabelText("Exemplos")).toBeInTheDocument();
  });

  it("o botão limpa as mensagens e o aparelho e fica na tela de conversa, com o foco na barra", async () => {
    detect = () => ({ matches: [DB44], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "minha DB44 esquenta?");
    expect(await screen.findByText("Resposta do manual.")).toBeInTheDocument();
    expect(screen.getByText("DB44")).toBeInTheDocument(); // o chip

    await user.click(screen.getByRole("button", { name: /Nova conversa/ }));

    expect(screen.queryByText("Resposta do manual.")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tirar aparelho" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Qual é a sua dúvida?" })).not.toBeInTheDocument(); // sem tela inicial
    expect(screen.queryByLabelText("Exemplos")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Sua dúvida" })).toHaveFocus();
  });

  it("depois de limpar, a próxima pergunta vai sem o aparelho antigo", async () => {
    detect = (text) => (text.includes("DB44") ? { matches: [DB44], unrecognized: [], only_codes: false } : { matches: [], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "minha DB44 esquenta?");
    await screen.findByText("Resposta do manual.");
    await user.click(screen.getByRole("button", { name: /Nova conversa/ }));

    await ask(user, "quanto dura a garantia?");

    await waitFor(() => expect(asked).toHaveLength(2));
    expect(asked[1]).toEqual({ question: "quanto dura a garantia?" });
  });

  it("o logo volta à tela inicial, com o mascote e os exemplos", async () => {
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "quanto dura a garantia?");
    await screen.findByText("Resposta do manual.");

    await user.click(screen.getByRole("link", { name: /página inicial/ }));

    expect(screen.getByRole("heading", { name: "Qual é a sua dúvida?" })).toBeInTheDocument();
    expect(screen.getByLabelText("Exemplos")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Nova conversa/ })).not.toBeInTheDocument();
  });

  it("uma resposta que ainda estava a caminho não reaparece na conversa nova", async () => {
    let release: (value: object) => void = () => {};
    answer = () => new Promise((resolve) => (release = resolve));
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "quanto dura a garantia?");
    await waitFor(() => expect(asked).toHaveLength(1)); // a pergunta saiu e a resposta está pendente

    await user.click(screen.getByRole("button", { name: /Nova conversa/ }));
    release({ answer: "Resposta atrasada.", refused: false, citations: [] });
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(screen.queryByText("Resposta atrasada.")).not.toBeInTheDocument();
    expect(screen.queryByText("quanto dura a garantia?")).not.toBeInTheDocument();
  });
});

describe("Detecção do modelo no chat (spec 0001)", () => {
  it("o aparelho citado vira o chip e a pergunta leva manual_id e model_code (AC-8)", async () => {
    detect = () => ({ matches: [DB44], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);

    await ask(user, "minha DB44 esquenta?");

    await screen.findByText("Resposta do manual.");
    expect(asked[0]).toEqual({ question: "minha DB44 esquenta?", manual_id: electrolux.manual_id, model_code: "DB44" });
  });

  it("só o código escolhe o aparelho sem bolha e sem chamar a resposta (AC-14)", async () => {
    detect = () => ({ matches: [DB44], unrecognized: [], only_codes: true });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);

    await ask(user, "DB44");

    expect(await screen.findByRole("button", { name: "Tirar aparelho" })).toBeInTheDocument();
    expect(asked).toHaveLength(0);
    expect(screen.queryByText("DB44", { selector: "p.bg-ink" })).not.toBeInTheDocument();
  });

  it("dois aparelhos abrem a escolha, e escolher envia a pergunta com ele (AC-16)", async () => {
    detect = () => ({ matches: [DB44, BRE], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "DB44 ou BRE57FE, qual esquenta mais?");

    const turn = await screen.findByText("Qual destes é o seu aparelho?");
    expect(asked).toHaveLength(0);
    await user.click(within(turn.closest("article")!).getByRole("button", { name: /BRE57FE/ }));

    await screen.findByText("Resposta do manual.");
    expect(asked[0]).toMatchObject({ manual_id: brastemp.manual_id, model_code: "BRE57FE" });
  });

  it("'Nenhum destes' pergunta sem aparelho (AC-16)", async () => {
    detect = () => ({ matches: [DB44, BRE], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "DB44 ou BRE57FE, qual esquenta mais?");

    await user.click(await screen.findByRole("button", { name: "Nenhum destes" }));

    await screen.findByText("Resposta do manual.");
    expect(asked[0]).toEqual({ question: "DB44 ou BRE57FE, qual esquenta mais?" });
  });

  it("outro manual troca o chip e avisa (AC-17)", async () => {
    detect = (text) => ({ matches: [text.includes("BRE") ? BRE : DB44], unrecognized: [], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);
    await ask(user, "minha DB44 esquenta?");
    await screen.findByText("Resposta do manual.");

    await ask(user, "e a BRE57FE?");

    await waitFor(() => expect(productBar()).toHaveTextContent("Troquei para BRE57FE, geladeira Brastemp."));
    expect(productBar()).toHaveTextContent("BRE57FE");
  });

  it("código desconhecido avisa e anota, sem erro (AC-18 e spec 0003)", async () => {
    detect = () => ({ matches: [], unrecognized: ["XY99"], only_codes: false });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);

    await ask(user, "uso o XY99 aqui");

    await waitFor(() =>
      expect(productBar()).toHaveTextContent("Não reconheci XY99; respondi com todos os manuais. Anotei o modelo para a base crescer."),
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("a detecção que falha não bloqueia a pergunta (AC-9)", async () => {
    detect = () => {
      throw new Error("rede fora do ar");
    };
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);

    await ask(user, "quanto dura a garantia?");

    expect(await screen.findByText("Resposta do manual.")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("a recusa mostra a dica de como perguntar melhor (spec 0004, AC-6)", async () => {
    answer = () => ({ answer: "Não encontrei essa informação.", refused: true, citations: [] });
    const user = userEvent.setup();
    render(<Chat initialQuestion="" />);

    await ask(user, "pergunta fora do manual");

    expect(await screen.findByText(/Dica: descreva o que acontece com as palavras do manual/)).toBeInTheDocument();
  });
});
