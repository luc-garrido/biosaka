// Biosaka - Apiários e colmeias do usuário logado, consultados e cadastrados pela API.
// Precisa de auth.js e api.js carregados antes.
const $ = id => document.getElementById(id);
const esc = t => Object.assign(document.createElement("div"), {textContent: t}).innerHTML;
const hoje = () => new Date().toLocaleDateString("sv");
let apiarios = [];
let colmeias = [];
const campos = ["apiario", "codigo", "especie", "data"];
const camposApiario = ["apiario-nome", "apiario-local"];
const STATUS = {
  ativa: ["pronta", "Ativa"],
  em_observacao: ["sem-dados", "Em observação"],
  inativa: ["aguardar", "Inativa"]
};

exigirLogin();
const usuario = usuarioLogado() || {};
$("nome-usuario").textContent = usuario.nome || "";
$("sair").onclick = e => { e.preventDefault(); sair(); };
$("data").max = hoje();

function mostrar(tela) {
  for (const nome of ["lista", "form", "apiario"]) $("tela-" + nome).hidden = tela !== nome;
  scrollTo(0, 0);
}

function abrirForm() {
  if (!apiarios.length) return toast("Cadastre um apiário antes de cadastrar colmeias.", false);
  $("form").reset();
  campos.forEach(c => marcar(c, ""));
  mostrar("form");
  $("apiario").focus();
}

function abrirApiario() {
  $("form-apiario").reset();
  camposApiario.forEach(c => marcar(c, ""));
  mostrar("apiario");
  $("apiario-nome").focus();
}

function toast(texto, ok) {
  const t = $("toast");
  t.textContent = (ok ? "✔ " : "⚠ ") + texto;
  t.style.background = ok ? "var(--verde)" : "var(--vermelho)";
  t.hidden = false;
  setTimeout(() => t.hidden = true, 6000);
}

function renderizar() {
  $("lista").innerHTML = colmeias.length ? colmeias.map(c => {
    const [classe, texto] = STATUS[c.situacao];
    const apiario = apiarios.find(a => a.id === c.apiario_id);
    const data = c.data_instalacao ? c.data_instalacao.split("-").reverse().join("/") : "não informada";
    return `<div class="card"><h2>${esc(c.codigo)}</h2>
      <p>${esc(c.especie_abelha || "Espécie não informada")} · instalação: ${esc(data)}<br>
      ${esc(apiario ? apiario.nome : "Apiário " + c.apiario_id)}</p>
      <div class="status ${classe}">Situação cadastral: ${texto}</div>
      <a class="botao-link primario" href="detalhes.html?id=${c.id}">Ver detalhes</a>
      <button class="secundario" data-id="${c.id}">${c.situacao === "inativa" ? "Reativar" : "Desativar"}</button></div>`;
  }).join("") : `<div class="vazio"><h2>Nenhuma colmeia cadastrada</h2>
      <p>${apiarios.length ? "Clique em “+ Nova colmeia” para começar." : "Comece cadastrando seu primeiro apiário."}</p></div>`;
}

function preencherApiarios() {
  $("apiario").innerHTML = '<option value="">Selecione o apiário</option>' + apiarios.map(a =>
    `<option value="${a.id}">${esc(a.nome)}</option>`).join("");
  $("nova-colmeia").disabled = !apiarios.length;
}

async function carregar() {
  $("atualizar").disabled = true;
  $("nova-colmeia").disabled = true;
  $("lista").setAttribute("aria-busy", "true");
  $("lista").innerHTML = '<div class="card">Carregando colmeias...</div>';
  try {
    // shortcut: até 1000 registros por listagem; paginar quando o cadastro ultrapassar esse limite.
    const resultado = await Promise.all([
      requisitar("/apiarios?usuario_id=" + usuario.id + "&limite=1000"),
      requisitar("/colmeias?limite=1000")
    ]);
    apiarios = resultado[0];
    // Mostra só as colmeias dos apiários deste usuário
    const meus = new Set(apiarios.map(a => a.id));
    colmeias = resultado[1].filter(c => meus.has(c.apiario_id));
    preencherApiarios();
    renderizar();
    if (!apiarios.length) toast("Cadastre um apiário antes de cadastrar colmeias.", false);
    return true;
  } catch (erro) {
    apiarios = [];
    colmeias = [];
    $("lista").innerHTML = '<div class="vazio">Falha ao carregar. Confira os servidores e clique em Atualizar.</div>';
    toast(erro.message, false);
    return false;
  } finally {
    $("atualizar").disabled = false;
    $("lista").setAttribute("aria-busy", "false");
  }
}

function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}

function validar() {
  const codigo = $("codigo").value, data = $("data").value;
  const erros = {
    apiario: apiarios.some(a => a.id === Number($("apiario").value)) ? "" : "Selecione um apiário.",
    codigo: /^COL-\d{3}$/.test(codigo) ? "" : "Use o formato COL-000 (ex.: COL-004).",
    especie: $("especie").value ? "" : "Selecione a espécie.",
    data: !data || data < "1900-01-01" || data > hoje() ? "Informe uma data entre 1900 e hoje." : ""
  };
  campos.forEach(c => marcar(c, erros[c]));
  const primeiro = campos.find(c => erros[c]);
  if (primeiro) $(primeiro).focus();
  return !primeiro;
}

$("form").onsubmit = async e => {
  e.preventDefault();
  const botao = $("salvar");
  if (botao.disabled || !validar()) return;
  const nova = {
    apiario_id: Number($("apiario").value), codigo: $("codigo").value,
    especie_abelha: $("especie").value, data_instalacao: $("data").value, situacao: "ativa"
  };
  botao.disabled = true;
  botao.textContent = "Salvando...";
  try {
    const salva = await requisitar("/colmeias", "POST", nova);
    colmeias.push(salva);
    renderizar();
    mostrar("lista");
    toast("Colmeia cadastrada no banco com sucesso!", true);
  } catch (erro) {
    toast(erro.message, false);
  } finally {
    botao.disabled = false;
    botao.textContent = "Salvar colmeia";
  }
};

// ---------- Cadastro de apiário (POST /apiarios) ----------

$("form-apiario").onsubmit = async e => {
  e.preventDefault();
  const botao = $("salvar-apiario");
  if (botao.disabled) return;
  const nome = $("apiario-nome").value, local = $("apiario-local").value;
  const erros = {
    "apiario-nome": !nome.trim() ? "Informe o nome do apiário."
      : nome !== nome.trim() ? "Remova os espaços no início ou no fim."
      : nome.length > 120 ? "Use até 120 caracteres." : "",
    "apiario-local": local.length > 255 ? "Use até 255 caracteres." : ""
  };
  camposApiario.forEach(c => marcar(c, erros[c]));
  const primeiro = camposApiario.find(c => erros[c]);
  if (primeiro) return $(primeiro).focus();

  botao.disabled = true;
  botao.textContent = "Salvando...";
  try {
    const salvo = await requisitar("/apiarios", "POST",
      {usuario_id: usuario.id, nome, localizacao: local.trim() || null});
    apiarios.push(salvo);
    preencherApiarios();
    renderizar();
    mostrar("lista");
    toast("Apiário cadastrado! Agora você já pode cadastrar colmeias.", true);
  } catch (erro) {
    toast(erro.message, false);
  } finally {
    botao.disabled = false;
    botao.textContent = "Salvar apiário";
  }
};

$("lista").onclick = async e => {
  const botao = e.target.closest("button[data-id]");
  if (!botao || botao.disabled) return;
  botao.disabled = true;
  try {
    // PUT substitui o registro: buscar antes evita apagar tara e dados da rainha ausentes no formulário.
    const {id, ...dados} = await requisitar("/colmeias/" + botao.dataset.id);
    dados.situacao = dados.situacao === "inativa" ? "ativa" : "inativa";
    const salva = await requisitar("/colmeias/" + id, "PUT", dados);
    colmeias = colmeias.map(c => c.id === salva.id ? salva : c);
    renderizar();
    toast("Situação atualizada no banco!", true);
  } catch (erro) {
    toast(erro.message, false);
  } finally {
    botao.disabled = false;
  }
};

carregar();
