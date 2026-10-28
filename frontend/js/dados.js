// Biosaka - Dados das colmeias, usados por mais de uma página
// Sem banco de dados: ficam no localStorage, começando com colmeias de exemplo


// =====================================================================
// ARMAZENAMENTO DE INFORMAÇÕES — VINCULAR O DATASET AQUI
// ---------------------------------------------------------------------
// Hoje as colmeias ficam no localStorage e começam com as DE EXEMPLO
// abaixo (funciona sem servidor, apenas para demonstração).
// Para usar o dataset real, troque o corpo de lerColmeias() e
// salvarColmeias() (no fim deste arquivo) pela leitura/gravação no
// dataset. Exemplo (comentado, para ser ativado depois):
//
//   const resposta = await fetch("URL_DO_DATASET_DE_COLMEIAS_AQUI");
//   const colmeias = await resposta.json();
//
// Campos de cada colmeia:
//   codigo    → "COL-000"
//   apelido   → texto (opcional)
//   especie   → "Nome comum (Nome Científico)"
//   regiao    → { cidade, estado, pais }
//   data      → "AAAA-MM-DD" (data de instalação)
//   status    → "pronta" | "aguardar" | "sem-dados"
//   sensor    → { peso, temperatura, umidade } ou null
//   historico → [{ data: "AAAA-MM-DD", texto }]
// =====================================================================

const CHAVE_COLMEIAS = "biosaka_colmeias";

// Próximo passo de cada status e em quantos dias ele é sugerido a partir de hoje.
// A data é só uma SUGESTÃO (de 7 a 14 dias, para termos uma semana de folga).
const PROXIMO_PASSO = {
  pronta: { acao: "Coletar o mel", dias: 7 },
  "sem-dados": { acao: "Conferir a instalação do sensor", dias: 10 },
  aguardar: { acao: "Reavaliar a colmeia", dias: 14 }
};

// Data sugerida para o próximo passo, no formato DD/MM/AAAA
function dataSugerida(status) {
  const d = new Date();
  d.setDate(d.getDate() + PROXIMO_PASSO[status].dias);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

// Região no formato "Cidade, Estado, País" (colmeias antigas podem não ter região)
function textoRegiao(colmeia) {
  const r = colmeia.regiao;
  return r ? `${r.cidade}, ${r.estado}, ${r.pais}` : "Região não informada";
}

// Colmeias de exemplo, com leituras do sensor e histórico fictícios
const COLMEIAS_EXEMPLO = [
  {
    codigo: "COL-001",
    apelido: "Jardim",
    especie: "Abelha-europeia (Apis Mellifera)",
    regiao: { cidade: "Campinas", estado: "São Paulo", pais: "Brasil" },
    data: "2025-03-12",
    status: "pronta",
    sensor: { peso: "38,2 kg", temperatura: "34,6 °C", umidade: "58%" },
    historico: [
      { data: "2026-10-20", texto: "Alimentação reforçada" },
      { data: "2026-10-05", texto: "Revisão geral da colmeia" },
      { data: "2025-03-12", texto: "Colmeia instalada" }
    ]
  },
  {
    codigo: "COL-002",
    apelido: "Rio",
    especie: "Jataí (Tetragonisca Angustula)",
    regiao: { cidade: "Piracicaba", estado: "São Paulo", pais: "Brasil" },
    data: "2025-05-20",
    status: "aguardar",
    sensor: { peso: "21,7 kg", temperatura: "32,9 °C", umidade: "71%" },
    historico: [
      { data: "2026-10-18", texto: "Colheita parcial de mel" },
      { data: "2026-09-30", texto: "Divisão da colmeia" },
      { data: "2025-05-20", texto: "Colmeia instalada" }
    ]
  },
  {
    codigo: "COL-003",
    apelido: "",
    especie: "Mandaçaia (Melipona Quadrifasciata)",
    regiao: { cidade: "Atibaia", estado: "São Paulo", pais: "Brasil" },
    data: "2025-08-02",
    status: "pronta",
    sensor: { peso: "35,0 kg", temperatura: "35,1 °C", umidade: "60%" },
    historico: [
      { data: "2026-10-12", texto: "Visita de rotina" },
      { data: "2025-08-02", texto: "Colmeia instalada" }
    ]
  }
];


// Devolve as colmeias salvas ou, se não houver nenhuma salva, as de exemplo
function lerColmeias() {
  try {
    const salvas = JSON.parse(localStorage.getItem(CHAVE_COLMEIAS));
    if (salvas) return salvas;
  } catch (erro) {
    // sem armazenamento: usa os exemplos
  }
  return COLMEIAS_EXEMPLO.slice();
}

// Salva a lista de colmeias no navegador
function salvarColmeias(colmeias) {
  try {
    localStorage.setItem(CHAVE_COLMEIAS, JSON.stringify(colmeias));
  } catch (erro) {
    // sem armazenamento: as colmeias não serão lembradas
  }
}
