// Biosaka - Funções de conta e sessão
// Sem servidor: contas e sessão ficam no localStorage. Apenas demonstração, não é seguro.


// =====================================================================
// ARMAZENAMENTO DE INFORMAÇÕES — VINCULAR O DATASET AQUI
// ---------------------------------------------------------------------
// Hoje as contas e a sessão ficam no localStorage do navegador
// (funciona sem servidor, mas serve apenas para demonstração).
// Para usar o dataset real, troque o corpo das funções lerContas(),
// salvarContas(), lerSessao(), iniciarSessao() e encerrarSessao() por
// chamadas ao dataset/API. Exemplo (comentado, para ser ativado depois):
//
//   const resposta = await fetch("URL_DO_DATASET_DE_CONTAS_AQUI");
//   const contas = await resposta.json();
//
// Campos de cada conta: usuario, email, telefone, cidade, estado, pais, senha
// (em produção a senha NUNCA deve ser guardada em texto puro).
// =====================================================================
const CHAVE_CONTAS = "biosaka_contas";
const CHAVE_SESSAO = "biosaka_sessao";


// ---------- Contas cadastradas ----------

function lerContas() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE_CONTAS)) || [];
  } catch (erro) {
    return [];
  }
}

function salvarContas(contas) {
  try {
    localStorage.setItem(CHAVE_CONTAS, JSON.stringify(contas));
    return true;
  } catch (erro) {
    return false;
  }
}


// ---------- Sessão ----------

function lerSessao() {
  try {
    return localStorage.getItem(CHAVE_SESSAO);
  } catch (erro) {
    return null;
  }
}

function iniciarSessao(usuario) {
  try {
    localStorage.setItem(CHAVE_SESSAO, usuario);
  } catch (erro) {
    // sem armazenamento: o login não será lembrado
  }
}

function encerrarSessao() {
  try {
    localStorage.removeItem(CHAVE_SESSAO);
  } catch (erro) {
    // nada a fazer
  }
}


// ---------- Validação compartilhada (sem autocorreção) ----------
// Nada é cortado, trocado ou ajustado em silêncio: se o valor está errado,
// a função devolve a mensagem de erro (ou "" quando está tudo certo).

// Valida cidade, estado ou país. "rotulo" é o texto do pedido (ex.: "a cidade")
function erroDeLugar(valor, rotulo) {
  if (!valor.trim()) return `Informe ${rotulo}.`;
  if (valor !== valor.trim() || /\s{2,}/.test(valor))
    return "Remova os espaços extras (no início, no fim ou repetidos).";
  if (valor.length < 2 || valor.length > 60)
    return "Use de 2 a 60 caracteres.";
  if (!/^[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'’. -]*$/.test(valor))
    return "Use apenas letras, espaços, hífen, apóstrofo ou ponto.";
  return "";
}
