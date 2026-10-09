// Acha no texto da pergunta os códigos do registro. Roda no servidor pelo mesmo motivo do /api/ask:
// o navegador nunca vê o endereço da API nem o segredo de bypass da Vercel.

const API_URL = process.env.MANU_API_URL ?? "http://localhost:8000";
const BYPASS_SECRET = process.env.API_BYPASS_SECRET;

// O limite de chamadas da API vale por pessoa: repassa o IP de quem chamou o site.
function clientIp(request: Request): Record<string, string> {
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return ip ? { "x-manu-client-ip": ip } : {};
}

export async function POST(request: Request) {
  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/products/detect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(BYPASS_SECRET ? { "x-vercel-protection-bypass": BYPASS_SECRET } : {}),
        ...clientIp(request),
      },
      body: await request.text(),
      cache: "no-store",
    });
  } catch {
    return Response.json({ detail: "Serviço temporariamente indisponível." }, { status: 503 });
  }

  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
  });
}
