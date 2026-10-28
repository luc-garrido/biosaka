# Validacao do backend unificado em 28/10/2026

- Sete testes HTTP de integracao aprovados no MySQL 8.4 real, usando schema
  temporario separado de biosaka_v3_dev. O schema de teste foi removido ao final.
- Cadastros, edicao, inspecoes, exclusoes restringidas, validacao de entradas,
  senha em scrypt, chave de acesso, filtros e paginacao foram verificados.
- Leituras de teste preservaram timestamp repetido, valor negativo, valor
  ausente e precisao decimal. As credenciais nao aparecem nas respostas.
- pip check: nenhuma dependencia quebrada. compileall: concluido.
- Consulta HTTP com TestClient sobre o banco historico existente: seis tabelas
  compativeis, serie em kg com fuso desconhecido, 524.110 leituras e duas
  linhas preservadas no timestamp 2017-10-29 02:00:00.
- A consulta historica nao escreveu no banco. Dados em backend_mysql.json.
- Uvicorn executado em 127.0.0.1:8000: HTTP 200 em /health, /docs e consulta
  paginada da serie real (total 524.110). Requisicao sem chave: HTTP 401.

Essas verificacoes nao incluem frontend, JWT, autorizacao individual,
diagnosticos agronomicos nem implantacao publica. A chave local e administrativa.
