// Biosaka - Sessão do usuário
// A senha NUNCA fica no navegador: ela vai para a API, que devolve um token.
// Guardamos só o token (e o nome/id públicos do usuário, para mostrar "Olá, ...")
// no sessionStorage, que é apagado quando a aba é fechada.

const CHAVE_TOKEN = "biosaka_token";
const CHAVE_USUARIO = "biosaka_usuario";


// Faz o login na API e guarda o token. Lança um Error com a mensagem se falhar.
async function entrar(email, senha) {
  const resposta = await requisitar("/auth/login", "POST", {email, senha});
  try {
    sessionStorage.setItem(CHAVE_TOKEN, resposta.access_token);
    sessionStorage.setItem(CHAVE_USUARIO, JSON.stringify({
      id: resposta.usuario.id, nome: resposta.usuario.nome
    }));
  } catch (erro) {
    throw new Error("O navegador bloqueou o armazenamento da sessão.");
  }
}

// Apaga a sessão e volta para o login
function sair() {
  try {
    sessionStorage.removeItem(CHAVE_TOKEN);
    sessionStorage.removeItem(CHAVE_USUARIO);
  } catch (erro) {
    // nada a fazer
  }
  location.replace("login.html");
}

// Token atual ou null
function token() {
  try {
    return sessionStorage.getItem(CHAVE_TOKEN);
  } catch (erro) {
    return null;
  }
}

// {id, nome} do usuário logado ou null
function usuarioLogado() {
  try {
    return JSON.parse(sessionStorage.getItem(CHAVE_USUARIO));
  } catch (erro) {
    return null;
  }
}

// Usado no topo das páginas logadas: sem token, vai para o login
function exigirLogin() {
  if (!token() || !usuarioLogado()) {
    location.replace("login.html");
    return false;
  }
  return true;
}
