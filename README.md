# BIOSAKA

Backend integrado ao modelo de seis tabelas MySQL e ao historico Beehive Metrics.
A pasta backend/ e a unica implementacao de backend neste repositorio.

## Modelo oficial

| Tabela | Conteudo |
| --- | --- |
| usuarios | Nome, telefone unico, email opcional e hash da senha |
| apiarios | Locais pertencentes a um usuario |
| colmeias | Codigo unico por apiario, situacao e tara opcional |
| inspecoes | Observacoes manuais, com campos nao avaliados explicitos |
| series_dataset | Origem, metrica, unidade, fuso e checksum do CSV |
| leituras | Valores e timestamps originais, sem eliminar horarios repetidos |

SQL em database/v3/01_cadastros.sql e 02_medicoes.sql.
Nao executar os antigos modelos de cinco/doze tabelas sobre este banco.
O backend nao executa create_all nem migracoes automaticamente.

## Executar localmente

Requisitos: Python 3.11+, Docker Desktop ativo e porta 3307 disponivel.
A partir da raiz deste repositorio:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item database/v3/.env.example database/v3/.env
```

Na primeira configuracao, preencher as duas senhas e BIOSAKA_API_TOKEN com
valores aleatorios diferentes. A chave da API deve ter pelo menos 32 caracteres.
Se o arquivo .env ja existir, preserva-lo; o ambiente local deste trabalho
ja esta configurado. Nao publicar esse arquivo.

```powershell
docker compose -f database/v3/compose.yaml up -d --wait
.venv/Scripts/python.exe -m uvicorn backend.app.main:site --host 127.0.0.1 --port 8000
```

Documentacao interativa: http://127.0.0.1:8000/docs.
Clicar Authorize e informar BIOSAKA_API_TOKEN. O cabecalho de acesso e X-API-Key.
GET /health consulta o servidor e confere as seis tabelas e suas colunas.

A conexao padrao usa 127.0.0.1:3307, banco biosaka_v3_dev, usuario biosaka.
Senhas sao carregadas de database/v3/.env; nomes/host/porta podem ser definidos
por BIOSAKA_DB_NAME, BIOSAKA_DB_HOST, BIOSAKA_DB_PORT e BIOSAKA_DB_USER.

O volume biosaka-v3_mysql_data e o mesmo usado na importacao local anterior.
Nao executar down -v para atualizar codigo: isso removeria os dados.
Scripts de inicializacao so rodam em volume vazio. Um banco antigo diferente
precisa de migracao revisada ou de um schema novo; nao e convertido automaticamente.

## Endpoints

Todas as rotas de dados exigem a chave administrativa local.

- GET /health: conexao e estrutura.
- POST/GET /usuarios: cadastro e consulta sem expor senha/hash.
- POST/GET /apiarios; PUT/DELETE /apiarios/{id}.
- POST/GET /colmeias; GET/PUT/DELETE /colmeias/{id}.
- POST/GET /inspecoes; PUT/DELETE /inspecoes/{id}.
- GET /series?colmeia_id=9.
- GET /series/{id}/leituras?inicio=2017-01-01&fim=2017-01-31T23:59:59&limite=100&offset=0.

Listagens tem limite de 100 por padrao, maximo de 1000, e offset.
A consulta de leituras devolve total, paginacao e metadados da serie.
Datas sao inclusivas e interpretadas no horario original da fonte.
Filtros com fuso sao rejeitados enquanto o fuso do dataset for desconhecido.
Decimais sao enviados como strings no JSON para conservar precisao.

POST/PUT usam os campos oficiais do modelo; campos antigos nome/localizacao
da colmeia nao sao aceitos. Use apiario_id e codigo. PUT substitui os campos
editaveis do registro inteiro e nao permite transferir a propriedade.
DELETE e bloqueado com HTTP 409 quando ha dependentes; para uma colmeia
com historico, preferir situacao=inativa.

POST /leituras e endpoints de manejo/status preditivo foram retirados:
o modelo atual recebe medicoes pelo importador e registra inspecoes separadamente.
Nenhum timestamp ou medicao do dataset e sobrescrito pela API.

## Dataset

Fonte: https://www.kaggle.com/datasets/se18m502/bee-hive-metrics.
Baixar o ZIP e colocar em data/raw/beehive-metrics.zip (ignorado pelo Git).
A descricao da versao 3 identifica weight_2017.csv em kg, Wurzburg, 2017;
o fuso nao e informado. A licenca nos metadados e Unknown; nao se afirma
permissao de redistribuicao do arquivo original.

```powershell
.venv/Scripts/python.exe database/v3/importar_peso.py --validar-apenas
.venv/Scripts/python.exe database/v3/importar_peso.py
```

A importacao cria uma conta tecnica bloqueada para login e uma colmeia
WURZBURG-2017. Importacao inicial: 524.110 linhas, 507 pesos negativos
para revisao e 60 horarios repetidos preservados. Reimportacao do mesmo
arquivo nao duplica linhas; checksum/conteudo alterado e rejeitado.
Relatorios historicos de outubro em database/v3/; nao comprovam por si
so o estado de outro ambiente. Consultas em database/v3/ver_peso_no_workbench.sql.

## Testes

Teste da tela de colmeias, sem dependências adicionais (Node.js 18+):

```powershell
node --test frontend/tests/colmeias.test.cjs
```

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest backend/tests -q
```

Os testes precisam do Docker/MySQL e criam biosaka_test_<identificador>
temporario, inicializado com os mesmos scripts SQL. Esse schema e removido
ao final; o banco biosaka_v3_dev e o dataset nao sao alterados.

## Limites atuais

API administrativa para uso local. A chave compartilhada nao substitui login
individual/JWT nem autorizacao por proprietario. A tela de colmeias consulta,
cadastra e altera a situacao pela API; as demais telas ainda usam demonstracao local.
Nao ha diagnostico integrado, previsao agronomica, hardware, clima
nem envio de WhatsApp nesta implementacao.

## Demonstrar a integracao de colmeias

Com MySQL e API iniciados conforme acima, abra outro terminal na raiz:

```powershell
.venv/Scripts/python.exe frontend/servidor.py
```

1. Abra http://127.0.0.1:5173/login.html e entre pela conta de demonstracao local.
2. A tela de colmeias carrega automaticamente. O servidor local encaminha as chamadas
   /api para a FastAPI, lendo a chave do .env. A chave nao vai para o JavaScript,
   para o armazenamento nem para as requisicoes do navegador.
3. Selecione um apiario existente, cadastre uma colmeia e recarregue para
   conferir a persistencia. Sem apiarios, crie primeiro usuario e apiario pelo Swagger.
4. Use Desativar/Reativar e confira a situacao apos recarregar. A alteracao preserva
   os campos de tara e rainha, sem excluir historico.

No painel de rede devem aparecer GET /api/apiarios, GET /api/colmeias, POST /api/colmeias e
GET/PUT /api/colmeias/{id}. A listagem mostra ate 1000 registros e a situacao cadastral;
nao mostra diagnostico preditivo. Esta demonstracao administrativa acessa todos os
registros da API: a sessao local nao restringe os dados por apicultor.

O servidor da interface escuta somente em 127.0.0.1:5173, rejeita Host e origem
externos e encaminha apenas consulta de apiarios e consulta/cadastro/alteracao de
colmeias. As rotas originais da FastAPI continuam exigindo X-API-Key, inclusive no
Swagger. Este servidor e um console local, nao uma solucao de autenticacao para
publicacao na Internet. Login individual e autorizacao por proprietario continuam
pendentes. Use frontend/servidor.py; o servidor estatico http.server nao encaminha /api.
