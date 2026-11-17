// Biosaka - Conversa com a API (usado por todas as páginas que falam com o backend)
// Precisa de auth.js carregado antes (usa token() e sair()).

const API_URL = "/api";

// Faz a requisição, envia o token e devolve o JSON da resposta.
// Em caso de erro, lança um Error com uma mensagem pronta para mostrar ao usuário.
async function requisitar(caminho, metodo = "GET", dados) {
  const cabecalhos = {};
  if (dados) cabecalhos["Content-Type"] = "application/json";
  const atual = token();
  if (atual) cabecalhos["Authorization"] = "Bearer " + atual;

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, {
      method: metodo,
      headers: cabecalhos,
      ...(dados ? {body: JSON.stringify(dados)} : {}),
      signal: AbortSignal.timeout(15000)
    });
  } catch (erro) {
    throw new Error("Não foi possível acessar a API. Confira o servidor e tente novamente.");
  }

  let corpo = null;
  if (resposta.status !== 204) {
    try {
      corpo = await resposta.json();
    } catch (erro) {
      corpo = null;
    }
  }

  if (!resposta.ok) {
    const detalhe = corpo && corpo.detail;
    // 401 fora do login = token vencido ou inválido: encerra a sessão
    if (resposta.status === 401 && caminho !== "/auth/login") {
      sair();
      throw new Error("Sua sessão expirou. Entre novamente.");
    }
    const mensagem =
      resposta.status === 409 ? "Registro duplicado ou com dependências (ex.: colmeia com inspeções)."
      : resposta.status === 422 && Array.isArray(detalhe)
        ? "Campos inválidos: " + detalhe.map(e => e.msg).join("; ")
      : resposta.status === 503 ? (detalhe || "API ou banco indisponível. Tente novamente em instantes.")
      : typeof detalhe === "string" ? detalhe
      : "Não foi possível concluir a operação.";
    const erro = new Error(mensagem);
    erro.status = resposta.status;
    throw erro;
  }
  return corpo;
}
