// Biosaka - Lógica da página de criação de conta (POST /api/usuarios)
// A senha é enviada uma única vez para a API, que guarda apenas o hash.


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

const campos = ["nome", "email", "telefone", "senha", "confirmar"];

// Mostra ou limpa o erro de um campo
function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}

// "(11) 91234-5678" → "+5511912345678" (formato internacional que a API exige)
const telefoneInternacional = telefone => "+55" + telefone.replace(/\D/g, "");


// ---------- Validação do formulário ----------

function validar() {
  // Sem autocorreção: os valores são lidos exatamente como foram digitados
  const nome = $("nome").value;
  const email = $("email").value;
  const telefone = $("telefone").value;
  const senha = $("senha").value;
  const confirmar = $("confirmar").value;

  const erros = {
    nome: !nome.trim()
      ? "Informe seu nome."
      : nome !== nome.trim() || /\s{2,}/.test(nome)
        ? "Remova os espaços extras (no início, no fim ou repetidos)."
        : nome.length < 2 || nome.length > 120
          ? "Use de 2 a 120 caracteres."
          : "",
    email: !email
      ? "Informe o e-mail."
      : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
        ? "Digite um e-mail válido (ex.: nome@email.com)."
        : "",
    telefone: !telefone
      ? "Informe o telefone."
      : !/^\([1-9]\d\) (9\d{4}|\d{4})-\d{4}$/.test(telefone)
        ? "Use o formato (11) 91234-5678."
        : "",
    senha: !senha
      ? "Crie uma senha."
      : senha.length < 8
        ? "A senha deve ter pelo menos 8 caracteres."
        : "",
    confirmar: !confirmar
      ? "Confirme a senha."
      : confirmar !== senha
        ? "As senhas não são iguais."
        : ""
  };

  campos.forEach(c => marcar(c, erros[c]));

  const primeiro = campos.find(c => erros[c]);
  if (primeiro) $(primeiro).focus();

  return !primeiro;
}


// ---------- Envio do formulário ----------

$("form").onsubmit = async e => {
  e.preventDefault();
  $("erro-geral").textContent = "";
  if (!validar()) return;

  const botao = $("continuar");
  botao.disabled = true;
  botao.textContent = "Criando conta...";
  try {
    await requisitar("/usuarios", "POST", {
      nome: $("nome").value,
      telefone: telefoneInternacional($("telefone").value),
      email: $("email").value,
      senha: $("senha").value
    });
    // Volta ao login com o aviso de conta criada
    location.href = "login.html?cadastro=ok";
  } catch (erro) {
    $("erro-geral").textContent = erro.status === 409
      ? "Esse e-mail ou telefone já está cadastrado."
      : erro.message;
  } finally {
    botao.disabled = false;
    botao.textContent = "Continuar";
  }
};
