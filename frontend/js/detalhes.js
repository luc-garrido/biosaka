// Biosaka - Lógica da página de detalhes das colmeias


// ---------- Funções auxiliares ----------

// Atalho para document.getElementById
const $ = id => document.getElementById(id);

// Escapa o texto digitado antes de inseri-lo no HTML
const esc = t => Object.assign(document.createElement("div"), {textContent: t}).innerHTML;

// Transforma AAAA-MM-DD em DD/MM/AAAA
const formatarData = iso => iso.split("-").reverse().join("/");


// ---------- Sessão ----------

// Sem login, volta para a tela de login
if (!lerSessao()) {
  location.replace("login.html");
}

$("sair").onclick = encerrarSessao;


// ---------- Recomendação de cada status ----------

const RECOMENDACOES = {
  pronta: {
    titulo: "✔ Pronta para a coleta",
    passo: "Agende a colheita e confira o peso antes de abrir a colmeia."
  },
  aguardar: {
    titulo: "✖ Melhor aguardar",
    passo: "Aguarde o peso aumentar e confira as leituras novamente na data sugerida."
  },
  "sem-dados": {
    titulo: "… Aguardando dados do sensor",
    passo: "Instale o sensor na colmeia para receber as primeiras leituras."
  }
};


// ---------- Montagem da página ----------

// Peso, temperatura e umidade, ou um aviso se ainda não houver leituras
function blocoSensor(sensor) {
  if (!sensor) return '<p class="sem-leitura">Ainda não há leituras do sensor.</p>';

  return `<div class="leituras">
      <div class="leitura"><span>Peso</span><strong>${sensor.peso}</strong></div>
      <div class="leitura"><span>Temperatura</span><strong>${sensor.temperatura}</strong></div>
      <div class="leitura"><span>Umidade</span><strong>${sensor.umidade}</strong></div>
    </div>`;
}

// Com ?codigo=COL-001 na página, mostra só essa colmeia; sem isso, mostra todas
const codigoPedido = new URLSearchParams(location.search).get("codigo");

// Um card completo para cada colmeia
function renderizar() {
  let colmeias = lerColmeias();

  if (codigoPedido) {
    colmeias = colmeias.filter(c => c.codigo === codigoPedido);

    $("titulo").textContent = "Detalhes da colmeia";
    $("subtitulo").textContent = "Leituras do sensor, histórico e recomendação desta colmeia.";

    if (!colmeias.length) {
      $("detalhes").innerHTML = `<div class="vazio">
        <h2>Colmeia não encontrada</h2>
        <p class="suave">Não existe nenhuma colmeia com o código ${esc(codigoPedido)}.</p>
        <a class="botao-link primario" href="colmeias.html">Ver minhas colmeias</a>
      </div>`;
      return;
    }
  }

  $("detalhes").innerHTML = colmeias.length ? colmeias.map(c => {
    const rec = RECOMENDACOES[c.status];
    const apelido = c.apelido ? ` <small>· ${esc(c.apelido)}</small>` : "";
    const eventos = (c.historico || []).map(h =>
      `<li><span>${formatarData(h.data)}</span>${esc(h.texto)}</li>`
    ).join("");

    return `<article class="detalhe">
      <h2>${esc(c.codigo)}${apelido}</h2>
      <p class="detalhe-info">${esc(c.especie)} · instalada em ${formatarData(c.data)}<br>
      Região: ${esc(textoRegiao(c))}</p>

      <div class="status ${c.status}">${rec.titulo}</div>
      <p class="passo">Próximo passo: <strong>${PROXIMO_PASSO[c.status].acao}</strong>. ${rec.passo}<br>
      Data prevista (sugestão): ${dataSugerida(c.status)}</p>

      <h3>Leituras do sensor</h3>
      ${blocoSensor(c.sensor)}

      <h3>Histórico de atividades</h3>
      <ul class="historico">${eventos}</ul>
    </article>`;
  }).join("") : `<div class="vazio">
    <h2>Você ainda não tem colmeias</h2>
    <a class="botao-link primario" href="colmeias.html">Cadastrar primeira colmeia</a>
  </div>`;
}


// ---------- Início ----------

renderizar();
