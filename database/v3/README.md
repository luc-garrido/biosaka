# Banco oficial de seis tabelas

Este e o unico modelo ativo do repositorio. Executar 01_cadastros.sql e
02_medicoes.sql nessa ordem apenas em schema novo. O compose.yaml inicializa
um volume vazio automaticamente, usando o schema biosaka_v3_dev.
Uma instalacao antiga de cinco/doze tabelas precisa de migracao propria:
nao executar esses scripts sobre dados existentes nem apagar o volume.

O ambiente local reutiliza o volume biosaka-v3_mysql_data e suas 524.110
leituras ja importadas. A API usa exatamente esses nomes e campos.
As versoes antigas continuam recuperaveis no historico Git.

- usuarios -> apiarios -> colmeias -> inspecoes.
- colmeias -> series_dataset -> leituras.
- Exclusoes com dependentes sao restringidas.
- Codigo de colmeia e unico por apiario.
- Leituras importadas sao identificadas por serie e linha original;
  timestamp nao e unico. Arquivo, checksum, unidade e fuso pertencem a serie.
- Valores ausentes ficam NULL; negativos sao preservados para revisao.
- DECIMAL(24,12) conserva 12 casas; o texto original guarda a precisao da fonte.

Configuracao privada em .env, ignorada pelo Git. Instrucao de instalacao,
endpoints, limites e testes no README.md da raiz do repositorio.
O importador usa biblioteca padrao do Python e cliente MySQL do container.
Arquivo original esperado em data/raw/beehive-metrics.zip, fora do Git.

As evidencias de importacao desta pasta registram execucoes anteriores.
A evidencia da API integrada esta em docs/evidencias/backend_mysql.json.
Nao ha credenciais nos relatorios. ver_peso_no_workbench.sql fornece consultas
para conferir origem, contagens e medicoes no Workbench.
