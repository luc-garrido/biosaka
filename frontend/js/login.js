// Biosaka - Lógica da página de login (POST /api/auth/login)


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

// Mostra ou limpa o erro de um campo
function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}


// ---------- Aviso de conta criada ----------

if (new URLSearchParams(location.search).get("cadastro") === "ok") {
  $("aviso").hidden = false;
}

// Já logado? Vai direto para as colmeias
if (token() && usuarioLogado()) location.replace("colmeias.html");


// ---------- Envio do formulário ----------

$("form").onsubmit = async e => {
  e.preventDefault();
  $("erro-geral").textContent = "";

  // Sem autocorreção: o valor vale exatamente como digitado
  const email = $("email").value;
  const senha = $("senha").value;

  marcar("email", !email.trim()
    ? "Informe seu e-mail."
    : email !== email.trim()
      ? "Remova os espaços no início ou no fim."
      : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
        ? "Digite um e-mail válido (ex.: nome@email.com)."
        : "");
  marcar("senha", senha ? "" : "Informe sua senha.");
  if ($("erro-email").textContent || !senha) return;

  const botao = $("entrar");
  botao.disabled = true;
  botao.textContent = "Entrando...";
  try {
    await entrar(email, senha);
    location.href = "colmeias.html";
  } catch (erro) {
    // 401 (senha errada) e 422 (senha curta demais) recebem a mesma mensagem
    $("erro-geral").textContent = erro.status === 401 || erro.status === 422
      ? "E-mail ou senha incorretos."
      : erro.message;
    $("email").setAttribute("aria-invalid", "");
    $("senha").setAttribute("aria-invalid", "");
  } finally {
    botao.disabled = false;
    botao.textContent = "Entrar";
  }
};
