// Biosaka - Detalhes de UMA colmeia, lidos da API (detalhes.html?id=9)
// Precisa de auth.js e api.js carregados antes.


// ---------- Funções auxiliares ----------

const $ = id => document.getElementById(id);
const esc = t => Object.assign(document.createElement("div"), {textContent: t}).innerHTML;
const hoje = () => new Date().toLocaleDateString("sv");
const formatarData = iso => iso.slice(0, 10).split("-").reverse().join("/");

const TEXTOS = {
  fraca: "fraca", media: "média", forte: "forte",
  observada: "observada", nao_observada: "não observada",
  baixa: "baixa", adequada: "adequada", nao_avaliada: "não avaliada"
};
const SITUACAO = {ativa: "Ativa", em_observacao: "Em observação", inativa: "Inativa"};

function toast(texto, ok) {
  const t = $("toast");
  t.textContent = (ok ? "✔ " : "⚠ ") + texto;
  t.style.background = ok ? "var(--verde)" : "var(--vermelho)";
  t.hidden = false;
  setTimeout(() => t.hidden = true, 6000);
}

function marcar(campo, mensagem) {
  $("erro-" + campo).textContent = mensagem;
  $(campo).toggleAttribute("aria-invalid", !!mensagem);
}


// ---------- Sessão e id da URL ----------

exigirLogin();
$("sair").onclick = e => { e.preventDefault(); sair(); };

const id = Number(new URLSearchParams(location.search).get("id"));
let colmeia = null;
let serie = null;
let grafico = null;


// ---------- 1. Dados da colmeia (GET /colmeias/{id}) ----------

async function carregarColmeia() {
  if (!Number.isInteger(id) || id <= 0) {
    $("subtitulo").textContent = "Colmeia não informada. Volte e escolha uma colmeia da lista.";
    return;
  }
  try {
    colmeia = await requisitar("/colmeias/" + id);
  } catch (erro) {
    $("subtitulo").textContent = erro.status === 404
      ? "Colmeia não encontrada." : erro.message;
    return;
  }
  $("titulo").textContent = "Colmeia " + colmeia.codigo;
  const instalacao = colmeia.data_instalacao ? formatarData(colmeia.data_instalacao) : "não informada";
  $("subtitulo").textContent = `${colmeia.especie_abelha || "Espécie não informada"} · instalada em ${instalacao} · situação: ${SITUACAO[colmeia.situacao]}`;
  $("conteudo").hidden = false;
  $("data-inspecao").max = hoje();

  carregarDiagnostico();
  carregarInspecoes();
  carregarSerie();
}


// ---------- 2. Diagnóstico (GET /colmeias/{id}/diagnostico) ----------
// Enquanto o backend não tiver essa rota, mostramos um aviso no lugar
// dos antigos cards de prontidão fictícios.

async function carregarDiagnostico() {
  try {
    const d = await requisitar("/colmeias/" + id + "/diagnostico");
    const cor = String(d.semaforo || "").toLowerCase();
    const regras = (d.detalhes_regras || []).filter(r => r.disparou !== false).map(r =>
      `<li>${esc(r.motivo || "")}${r.acao_sugerida ? " — " + esc(r.acao_sugerida) : ""}</li>`).join("");
    $("diagnostico").innerHTML = `<div class="semaforo ${esc(cor)}">${esc(d.semaforo || "—")}</div>
      <p>${esc(d.frase_modo_avo || "")}</p>
      ${regras ? `<ul>${regras}</ul>` : ""}
      <p class="sem-leitura">Confiança dos dados: ${esc(String(d.confianca || "—").toLowerCase())}</p>`;
  } catch (erro) {
    $("diagnostico").innerHTML = erro.status === 404
      ? '<p class="sem-leitura">Diagnóstico automático ainda não disponível para esta colmeia.</p>'
      : `<p class="sem-leitura">${esc(erro.message)}</p>`;
  }
}


// ---------- 3. Gráfico de peso (GET /series e /series/{id}/leituras) ----------

async function carregarSerie() {
  try {
    const series = await requisitar("/series?colmeia_id=" + id);
    serie = series.find(s => s.metrica === "weight") || series[0] || null;
  } catch (erro) {
    $("info-grafico").textContent = erro.message;
    return;
  }
  if (!serie) {
    $("info-grafico").textContent = "Esta colmeia ainda não tem leituras de sensor.";
    document.querySelector(".periodo").hidden = true;
    return;
  }
  desenhar(30);
}

// O dataset tem uma leitura por minuto. Para não baixar milhares de pontos,
// o período é dividido em janelas e pegamos as primeiras leituras de cada janela.
const AMOSTRAGEM = {7: {janelas: 42, limite: 60}, 30: {janelas: 60, limite: 30}, 365: {janelas: 73, limite: 15}};
const doisDigitos = n => String(n).padStart(2, "0");
// Data local sem fuso: o backend recusa horários com fuso (fuso do dataset desconhecido)
const semFuso = d => `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}T${doisDigitos(d.getHours())}:${doisDigitos(d.getMinutes())}:${doisDigitos(d.getSeconds())}`;

async function desenhar(dias) {
  document.querySelectorAll(".periodo button").forEach(b =>
    b.setAttribute("aria-pressed", String(Number(b.dataset.dias) === dias)));
  $("grafico").dataset.dias = dias;

  const fimEscolhido = $("fim-grafico").value || "2017-06-30";
  const fim = new Date(fimEscolhido + "T23:59:59");
  const inicio = new Date(fim.getTime() - dias * 864e5 + 1000);
  const {janelas, limite} = AMOSTRAGEM[dias];
  const passo = (fim - inicio) / janelas;

  $("info-grafico").textContent = "Carregando leituras…";
  try {
    const pedidos = [];
    for (let i = 0; i < janelas; i++) {
      const a = new Date(inicio.getTime() + i * passo);
      const b = new Date(inicio.getTime() + (i + 1) * passo - 1000);
      pedidos.push(() => requisitar(`/series/${serie.id}/leituras?inicio=${semFuso(a)}&fim=${semFuso(b)}&limite=${limite}`));
    }
    // No máximo 6 pedidos ao mesmo tempo, para não sobrecarregar a API
    const paginas = [];
    for (let i = 0; i < pedidos.length; i += 6) {
      paginas.push(...await Promise.all(pedidos.slice(i, i + 6).map(f => f())));
    }
    const pontos = paginas.flatMap(p => p.itens)
      .filter(l => l.valor_original !== null)
      .map(l => ({x: new Date(l.instante_original).getTime(), y: Number(l.valor_original)}));
    const total = paginas.reduce((soma, p) => soma + p.total, 0);

    $("info-grafico").textContent = pontos.length
      ? `${pontos.length} pontos exibidos de ${total} leituras no período (${formatarData(semFuso(inicio))} a ${formatarData(fimEscolhido)}). Horário original do dataset.`
      : "Sem leituras neste período. Experimente outra data (o dataset é de 2017).";
    montarGrafico(pontos);
  } catch (erro) {
    $("info-grafico").textContent = erro.message;
  }
}

function montarGrafico(pontos) {
  if (typeof Chart === "undefined") {
    $("info-grafico").textContent += " (Não foi possível carregar a biblioteca do gráfico — confira a internet.)";
    return;
  }
  if (grafico) grafico.destroy();
  grafico = new Chart($("grafico"), {
    type: "line",
    data: {datasets: [{label: "Peso (kg)", data: pontos, borderColor: "#E8960C",
      backgroundColor: "#E8960C", pointRadius: 0, borderWidth: 1.5, spanGaps: false}]},
    options: {
      responsive: true, maintainAspectRatio: false, parsing: false, animation: false,
      plugins: {legend: {display: false},
        tooltip: {callbacks: {title: itens => new Date(itens[0].parsed.x).toLocaleString("pt-BR")}}},
      scales: {
        x: {type: "linear", title: {display: true, text: "Data"},
          ticks: {maxTicksLimit: 8, callback: v => new Date(v).toLocaleDateString("pt-BR")}},
        y: {title: {display: true, text: "kg"}}
      }
    }
  });
}

document.querySelectorAll(".periodo button").forEach(b =>
  b.onclick = () => serie && desenhar(Number(b.dataset.dias)));
$("fim-grafico").onchange = () => serie && desenhar(Number($("grafico").dataset.dias || 30));


// ---------- 4. Inspeções (GET e POST /inspecoes) ----------

function itemInspecao(i) {
  return `<li><span>${formatarData(i.data_inspecao)}</span><div>
    Enxame ${TEXTOS[i.forca_enxame]} · postura ${TEXTOS[i.postura]} · reserva ${TEXTOS[i.reserva_alimentar]}
    ${i.observacoes ? "<br>" + esc(i.observacoes) : ""}</div></li>`;
}

async function carregarInspecoes() {
  $("inspecoes").innerHTML = "<li>Carregando…</li>";
  try {
    const lista = await requisitar("/inspecoes?colmeia_id=" + id);
    $("inspecoes").innerHTML = lista.length ? lista.map(itemInspecao).join("")
      : "<li>Nenhuma inspeção registrada ainda.</li>";
  } catch (erro) {
    $("inspecoes").innerHTML = `<li>${esc(erro.message)}</li>`;
  }
}

$("form-inspecao").onsubmit = async e => {
  e.preventDefault();
  const botao = $("salvar-inspecao");
  if (botao.disabled) return;
  const data = $("data-inspecao").value;
  const observacoes = $("observacoes").value;
  marcar("data-inspecao", !data || data < "1900-01-01" || data > hoje()
    ? "Informe uma data entre 1900 e hoje." : "");
  marcar("observacoes", observacoes.length > 2000 ? "Use até 2000 caracteres." : "");
  if ($("erro-data-inspecao").textContent || $("erro-observacoes").textContent) return;

  botao.disabled = true;
  botao.textContent = "Salvando...";
  try {
    await requisitar("/inspecoes", "POST", {
      colmeia_id: id, data_inspecao: data, forca_enxame: $("forca").value,
      postura: $("postura").value, reserva_alimentar: $("reserva").value, observacoes
    });
    $("form-inspecao").reset();
    toast("Inspeção registrada!", true);
    carregarInspecoes();
  } catch (erro) {
    toast(erro.message, false);
  } finally {
    botao.disabled = false;
    botao.textContent = "Salvar inspeção";
  }
};


// ---------- Início ----------

carregarColmeia();
