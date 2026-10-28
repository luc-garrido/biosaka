// Biosaka - Lógica da página de login


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

const campos = ["identificador", "senha"];

// Mostra ou limpa o erro de um campo
function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}


// ---------- Aviso de conta criada ----------

if (new URLSearchParams(location.search).get("cadastro") === "ok") {
  $("aviso").hidden = false;
}


// ---------- Envio do formulário ----------

$("form").onsubmit = e => {
  e.preventDefault();
  $("erro-geral").textContent = "";

  // Sem autocorreção: nada é cortado, o valor vale exatamente como digitado
  const identificador = $("identificador").value;
  const senha = $("senha").value;

  marcar("identificador", !identificador.trim()
    ? "Informe seu nome de usuário ou e-mail."
    : identificador !== identificador.trim()
      ? "Remova os espaços no início ou no fim."
      : "");
  marcar("senha", senha ? "" : "Informe sua senha.");
  if (!identificador.trim() || identificador !== identificador.trim() || !senha) return;

  // Procura uma conta pelo nome de usuário ou pelo e-mail
  const texto = identificador.toLowerCase();
  const conta = lerContas().find(c =>
    c.usuario.toLowerCase() === texto || c.email.toLowerCase() === texto
  );

  if (!conta || conta.senha !== senha) {
    $("identificador").setAttribute("aria-invalid", "");
    $("senha").setAttribute("aria-invalid", "");
    $("erro-geral").textContent = "Usuário ou senha incorretos.";
    return;
  }

  iniciarSessao(conta.usuario);
  location.href = "colmeias.html";
};
