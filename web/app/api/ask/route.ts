// A interface fala com a API por aqui, no servidor: o navegador nunca vê o endereço da API
// nem o segredo que atravessa a proteção de deploy da Vercel.

export const maxDuration = 60;

const API_URL = process.env.MANU_API_URL ?? "http://localhost:8000";
const BYPASS_SECRET = process.env.API_BYPASS_SECRET;

export async function POST(request: Request) {
  const body = await request.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(BYPASS_SECRET ? { "x-vercel-protection-bypass": BYPASS_SECRET } : {}),
      },
      body,
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
