// Biosaka - Lógica da tela de colmeias


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

// Escapa o texto digitado antes de inseri-lo no HTML
const esc = t => Object.assign(document.createElement("div"), {textContent: t}).innerHTML;

// Data de hoje no formato AAAA-MM-DD
const hoje = () => new Date().toLocaleDateString("sv");


// ---------- Sessão ----------

// Sem login, volta para a tela de login
if (!lerSessao()) {
  location.replace("login.html");
}

$("nome-usuario").textContent = lerSessao() || "";

$("sair").onclick = encerrarSessao;


// ---------- Dados ----------

const campos = ["codigo", "especie", "cidade", "estado", "pais", "data", "apelido"];

// Classe CSS e texto de cada status da colmeia
const STATUS = {
  pronta: ["pronta", "✔ Pronta para a coleta"],
  aguardar: ["aguardar", "✖ Melhor aguardar"],
  "sem-dados": ["sem-dados", "… Aguardando dados do sensor"]
};

// Colmeias salvas, ou as de exemplo na primeira vez
const colmeias = lerColmeias();


// ---------- Navegação entre telas ----------

function mostrar(tela) {
  $("tela-lista").hidden = tela !== "lista";
  $("tela-form").hidden = tela !== "form";

  scrollTo(0, 0);
}

function abrirForm() {
  $("form").reset();
  campos.forEach(c => marcar(c, ""));

  mostrar("form");
  $("codigo").focus();
}


// ---------- Mensagem de sucesso ou erro ----------

function toast(texto, ok) {
  const t = $("toast");

  t.textContent = (ok ? "✔ " : "⚠ ") + texto;
  t.style.background = ok ? "var(--verde)" : "var(--vermelho)";
  t.hidden = false;

  setTimeout(() => t.hidden = true, 4000);
}


// ---------- Listagem de colmeias ----------

function renderizar() {
  $("lista").innerHTML = colmeias.length ? colmeias.map(c => {
    const [classe, texto] = STATUS[c.status];

    const apelido = c.apelido ? ` <small>· ${esc(c.apelido)}</small>` : "";

    // A data aparece como DD/MM/AAAA
    return `<div class="card"><h2>${esc(c.codigo)}${apelido}</h2>
      <p>${esc(c.especie)} · instalada em ${c.data.split("-").reverse().join("/")}<br>
      ${esc(textoRegiao(c))}</p>
      <div class="status ${classe}">${texto}</div>
      <p class="proximo">Próximo passo: <strong>${PROXIMO_PASSO[c.status].acao}</strong><br>
      Data sugerida: ${dataSugerida(c.status)}</p>
      <a class="botao-link secundario" href="detalhes.html?codigo=${encodeURIComponent(c.codigo)}">Ver detalhes</a></div>`;
  }).join("") : `<div class="vazio"><div style="font-size:56px">🐝</div>
    <h2>Você ainda não tem colmeias</h2>
    <button class="primario" onclick="abrirForm()">Cadastrar primeira colmeia</button></div>`;
}

function carregar() {
  $("lista").innerHTML = '<div class="card"><div class="sk"></div><div class="sk" style="width:45%"></div><div class="sk" style="height:46px"></div></div>'.repeat(4);

  // Simula o tempo de resposta de um servidor
  setTimeout(renderizar, 1200);
}


// ---------- Validação do formulário ----------

function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}

function validar() {
  // Sem autocorreção: os valores são lidos exatamente como foram digitados.
  // Se algo estiver errado, aparece uma mensagem de erro (nada é cortado nem trocado).
  const codigo = $("codigo").value, data = $("data").value, apelido = $("apelido").value;

  const erros = {
    codigo: !codigo
      ? "Informe o código da colmeia."
      : !/^COL-\d{3}$/.test(codigo)
        ? "Use o formato COL-000, com letras maiúsculas e sem espaços (ex.: COL-004)."
        : "",
    especie: $("especie").value ? "" : "Selecione a espécie.",
    cidade: erroDeLugar($("cidade").value, "a cidade"),
    estado: erroDeLugar($("estado").value, "o estado"),
    pais: erroDeLugar($("pais").value, "o país"),
    data: !data
      ? "Informe uma data de instalação válida."
      : data < "1900-01-01"
        ? "Informe uma data a partir de 1900."
        : data > hoje()
          ? "A data não pode ser no futuro."
          : "",
    // Apelido é opcional, mas se for preenchido precisa ser válido
    apelido: !apelido
      ? ""
      : apelido !== apelido.trim() || /\s{2,}/.test(apelido)
        ? "Remova os espaços extras (no início, no fim ou repetidos)."
        : apelido.length > 30
          ? "Use no máximo 30 caracteres."
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

  if (!validar()) return;

  const nova = {
    codigo: $("codigo").value,
    apelido: $("apelido").value,
    especie: $("especie").value,
    regiao: {
      cidade: $("cidade").value,
      estado: $("estado").value,
      pais: $("pais").value
    },
    data: $("data").value,
    status: "sem-dados",
    sensor: null,
    historico: [{ data: $("data").value, texto: "Colmeia instalada" }]
  };

  const botao = $("salvar");
  botao.disabled = true;
  botao.innerHTML = '<span class="spinner"></span> Salvando...';

  // Simula o tempo de resposta de um servidor
  setTimeout(() => {
    botao.disabled = false;
    botao.textContent = "Salvar colmeia";

    if (colmeias.some(c => c.codigo === nova.codigo)) {
      marcar("codigo", "Já existe uma colmeia com esse código.");
      return toast("Não foi possível salvar. Tente novamente.", false);
    }

    // ONDE SALVAR NO DATASET: a nova colmeia é gravada em salvarColmeias() (ver dados.js)
    colmeias.push(nova);
    salvarColmeias(colmeias);
    toast("Colmeia cadastrada com sucesso!", true);
    mostrar("lista");
    carregar();
  }, 1000);
};


// ---------- Início ----------

carregar();
