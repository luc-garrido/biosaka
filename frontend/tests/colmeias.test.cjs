const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const vm = require('node:vm');

const codigo = ['auth.js', 'api.js', 'colmeias.js']
  .map(arquivo => readFileSync(join(__dirname, '../js', arquivo), 'utf8')).join('\n');
const evento = {preventDefault() {}};
const apiario = {id: 2, nome: 'Apiário de teste'};
const colmeia = {id: 7, apiario_id: 2, codigo: 'COL-001', situacao: 'ativa',
  especie_abelha: 'Apis mellifera', data_instalacao: null,
  origem_rainha: 'Criatório', data_introducao_rainha: '2025-01-01', peso_tara_kg: '4.125'};

function tela(responder) {
  const elementos = {};
  const elemento = id => elementos[id] ||= {value: '', disabled: false, hidden: false,
    style: {}, textContent: '', innerHTML: '', setAttribute() {}, toggleAttribute() {}, focus() {}, reset() {}};
  const chamadas = [];
  const sessao = new Map([['biosaka_token', 'token-de-teste'],
    ['biosaka_usuario', JSON.stringify({id: 5, nome: 'Teste'})]]);
  const navegacao = [];
  const contexto = vm.createContext({
    sessionStorage: {getItem: k => sessao.get(k) ?? null, setItem: (k, v) => sessao.set(k, v),
      removeItem: k => sessao.delete(k)},
    document: {getElementById: elemento, createElement() {
      return {textContent: '', get innerHTML() {
        return this.textContent.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
      }};
    }},
    scrollTo() {}, setTimeout() {},
    location: {replace: destino => navegacao.push(destino)}, AbortSignal,
    fetch: async (url, opcoes) => {
      chamadas.push({url, ...opcoes});
      const {status = 200, corpo} = await responder(url, opcoes);
      return {ok: status >= 200 && status < 300, status, json: async () => corpo};
    }
  });
  const carregamento = vm.runInContext(codigo, contexto);
  return {elemento, chamadas, contexto, sessao, navegacao,
    async carregar() { await carregamento; },
    preencher() {
      for (const [id, valor] of Object.entries({apiario: '2', codigo: 'COL-002', especie: 'Apis mellifera', data: '2025-01-01'})) {
        elemento(id).value = valor;
      }
    }
  };
}

function consulta(url) {
  return {corpo: url.includes('/apiarios') ? [apiario] : [colmeia]};
}

test('carrega automaticamente, escapa HTML e não envia chave administrativa', async () => {
  const t = tela(url => ({corpo: url.includes('/apiarios') ? [apiario] : [{...colmeia, codigo: '<script>x</script>'}]}));
  await t.carregar();
  assert.equal(t.chamadas.length, 2);
  assert.equal(t.chamadas[0].headers['X-API-Key'], undefined);
  assert.equal(t.chamadas[0].url, '/api/apiarios?usuario_id=5&limite=1000');
  assert.equal(t.chamadas[0].headers.Authorization, 'Bearer token-de-teste');
  assert.match(t.elemento('lista').innerHTML, /&lt;script&gt;/);
  assert.doesNotMatch(t.elemento('lista').innerHTML, /<script>/);
  assert.match(t.elemento('lista').innerHTML, /não informada/);
  assert.equal(t.elemento('nova-colmeia').disabled, false);
});

test('cadastro envia somente os campos aceitos e usa o registro devolvido pela API', async () => {
  const t = tela((url, opcoes) => opcoes.method === 'POST'
    ? {status: 201, corpo: {...colmeia, id: 8, codigo: 'COL-002'}} : consulta(url));
  await t.carregar(); t.preencher();
  await t.elemento('form').onsubmit(evento);
  const envio = t.chamadas.find(c => c.method === 'POST');
  assert.deepEqual(JSON.parse(envio.body), {apiario_id: 2, codigo: 'COL-002',
    especie_abelha: 'Apis mellifera', data_instalacao: '2025-01-01', situacao: 'ativa'});
  assert.match(t.elemento('lista').innerHTML, /COL-002/);
  assert.equal(t.elemento('salvar').disabled, false);
});

test('duplicidade não adiciona cadastro fictício e permite tentar novamente', async () => {
  const t = tela((url, opcoes) => opcoes.method === 'POST'
    ? {status: 409, corpo: {detail: 'Duplicado'}} : consulta(url));
  await t.carregar(); t.preencher();
  await t.elemento('form').onsubmit(evento);
  assert.doesNotMatch(t.elemento('lista').innerHTML, /COL-002/);
  assert.match(t.elemento('toast').textContent, /duplicado/i);
  assert.equal(t.elemento('salvar').disabled, false);
});

test('PUT preserva tara e rainha buscando o registro antes de atualizar', async () => {
  const t = tela((url, opcoes) => url.endsWith('/colmeias/7')
    ? {corpo: opcoes.method === 'PUT' ? {id: 7, ...JSON.parse(opcoes.body)} : colmeia} : consulta(url));
  await t.carregar();
  const botao = {dataset: {id: '7'}, disabled: false};
  await t.elemento('lista').onclick({target: {closest: () => botao}});
  const dados = JSON.parse(t.chamadas.find(c => c.method === 'PUT').body);
  assert.equal(dados.situacao, 'inativa');
  assert.equal(dados.peso_tara_kg, '4.125');
  assert.equal(dados.origem_rainha, 'Criatório');
  assert.equal(dados.data_introducao_rainha, '2025-01-01');
  assert.equal('id' in dados, false);
  assert.match(t.elemento('lista').innerHTML, /Situação cadastral: Inativa/);
});

test('401 (token vencido) apaga a sessão, volta ao login e não usa dados de exemplo', async () => {
  const t = tela(() => ({status: 401, corpo: {detail: 'Inválida'}}));
  await t.carregar();
  assert.equal(t.elemento('nova-colmeia').disabled, true);
  assert.match(t.elemento('toast').textContent, /sessão expirou/);
  assert.match(t.elemento('lista').innerHTML, /Falha ao carregar/);
  assert.equal(t.sessao.has('biosaka_token'), false);
  assert.ok(t.navegacao.length && t.navegacao.every(d => d === 'login.html'));
});

test('nenhuma senha ou conta fica guardada no navegador', () => {
  const auth = readFileSync(join(__dirname, '../js/auth.js'), 'utf8');
  assert.doesNotMatch(auth, /localStorage|CHAVE_CONTAS|senha\s*:/);
});

test('mostra só as colmeias dos apiários do usuário logado', async () => {
  const t = tela(url => ({corpo: url.includes('/apiarios') ? [apiario]
    : [colmeia, {...colmeia, id: 99, apiario_id: 50, codigo: 'COL-999'}]}));
  await t.carregar();
  assert.match(t.elemento('lista').innerHTML, /COL-001/);
  assert.doesNotMatch(t.elemento('lista').innerHTML, /COL-999/);
  assert.match(t.elemento('lista').innerHTML, /detalhes\.html\?id=7/);
});

test('cadastro de apiário usa o id do usuário logado', async () => {
  const t = tela((url, opcoes) => opcoes.method === 'POST'
    ? {status: 201, corpo: {id: 3, usuario_id: 5, nome: 'Sítio', localizacao: null}} : {corpo: []});
  await t.carregar();
  t.elemento('apiario-nome').value = 'Sítio';
  await t.elemento('form-apiario').onsubmit(evento);
  const envio = t.chamadas.find(c => c.method === 'POST');
  assert.equal(envio.url, '/api/apiarios');
  assert.deepEqual(JSON.parse(envio.body), {usuario_id: 5, nome: 'Sítio', localizacao: null});
  assert.equal(t.elemento('nova-colmeia').disabled, false);
});

test('falha de rede mostra erro e libera nova tentativa', async () => {
  const t = tela(() => {throw new Error('offline');});
  await t.carregar();
  assert.match(t.elemento('toast').textContent, /Não foi possível acessar a API/);
  assert.equal(t.elemento('atualizar').disabled, false);
});

test('sem apiários não habilita cadastro', async () => {
  const t = tela(() => ({corpo: []}));
  await t.carregar();
  assert.equal(t.elemento('nova-colmeia').disabled, true);
  assert.match(t.elemento('toast').textContent, /Cadastre um apiário/);
});

test('data futura e apiário inválido não fazem POST', async () => {
  const t = tela(consulta);
  await t.carregar(); t.preencher();
  t.elemento('data').value = '2999-01-01';
  await t.elemento('form').onsubmit(evento);
  assert.match(t.elemento('erro-data').textContent, /hoje/);
  t.elemento('data').value = '2025-01-01';
  t.elemento('apiario').value = '999';
  await t.elemento('form').onsubmit(evento);
  assert.match(t.elemento('erro-apiario').textContent, /Selecione/);
  assert.equal(t.chamadas.some(c => c.method === 'POST'), false);
});
