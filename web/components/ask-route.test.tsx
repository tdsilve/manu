import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/ask/route";

const request = () => new Request("http://web/api/ask", { method: "POST", body: JSON.stringify({ question: "oi" }) });

function upstream(status: number, headers: Record<string, string> = {}) {
  vi.stubGlobal("fetch", vi.fn(async () => Response.json({ detail: "corpo da API" }, { status, headers })));
}

beforeEach(() => vi.unstubAllGlobals());
afterEach(() => vi.unstubAllGlobals());

describe("POST /api/ask", () => {
  it("repassa o 429 com o corpo e o Retry-After da API (AC-06)", async () => {
    upstream(429, { "Retry-After": "42" });

    const response = await POST(request());

    expect(response.status).toBe(429);
    expect(response.headers.get("Retry-After")).toBe("42");
    expect(await response.json()).toEqual({ detail: "corpo da API" });
  });

  it("repassa o 429 sem inventar Retry-After quando a API não mandou", async () => {
    upstream(429);

    const response = await POST(request());

    expect(response.status).toBe(429);
    expect(response.headers.has("Retry-After")).toBe(false);
  });

  it("nos demais status não repassa Retry-After", async () => {
    upstream(503, { "Retry-After": "7" });

    const response = await POST(request());

    expect(response.status).toBe(503);
    expect(response.headers.has("Retry-After")).toBe(false);
  });
});
