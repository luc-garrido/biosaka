// Biosaka - Lógica da página de criação de conta


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

const campos = ["usuario", "email", "telefone", "cidade", "estado", "pais", "senha", "confirmar"];

// Mostra ou limpa o erro de um campo
function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}


// ---------- Validação do formulário ----------

function validar(contas) {
  // Sem autocorreção: os valores são lidos exatamente como foram digitados
  const usuario = $("usuario").value;
  const email = $("email").value;
  const telefone = $("telefone").value;
  const senha = $("senha").value;
  const confirmar = $("confirmar").value;

  // Compara ignorando maiúsculas e minúsculas
  const jaExiste = (campo, valor) =>
    contas.some(c => c[campo].toLowerCase() === valor.toLowerCase());

  const erros = {
    usuario: !usuario
      ? "Informe o nome de usuário."
      : !/^[\w.À-ÿ]{3,20}$/.test(usuario)
        ? "Use de 3 a 20 letras, números, ponto ou _ (sem espaços)."
        : jaExiste("usuario", usuario)
          ? "Esse nome de usuário já está em uso."
          : "",
    email: !email
      ? "Informe o e-mail."
      : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
        ? "Digite um e-mail válido (ex.: nome@email.com)."
        : jaExiste("email", email)
          ? "Esse e-mail já está cadastrado."
          : "",
    telefone: !telefone
      ? "Informe o telefone."
      : !/^\([1-9]\d\) (9\d{4}|\d{4})-\d{4}$/.test(telefone)
        ? "Use o formato (11) 91234-5678."
        : "",
    cidade: erroDeLugar($("cidade").value, "a cidade"),
    estado: erroDeLugar($("estado").value, "o estado"),
    pais: erroDeLugar($("pais").value, "o país"),
    senha: !senha
      ? "Crie uma senha."
      : senha.length < 6
        ? "A senha deve ter pelo menos 6 caracteres."
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

$("form").onsubmit = e => {
  e.preventDefault();
  $("erro-geral").textContent = "";

  const contas = lerContas();
  if (!validar(contas)) return;

  // ONDE SALVAR NO DATASET: aqui a nova conta é gravada (ver auth.js).
  contas.push({
    usuario: $("usuario").value,
    email: $("email").value,
    telefone: $("telefone").value,
    cidade: $("cidade").value,
    estado: $("estado").value,
    pais: $("pais").value,
    senha: $("senha").value
  });

  if (!salvarContas(contas)) {
    $("erro-geral").textContent = "Não foi possível salvar a conta. Tente novamente.";
    return;
  }

  // Volta ao login com o aviso de conta criada
  location.href = "login.html?cadastro=ok";
};
