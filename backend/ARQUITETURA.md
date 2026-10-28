# Arquitetura do MVP integrado

Modelo oficial: seis tabelas em database/v3/01_cadastros.sql e 02_medicoes.sql.

Usuario -> Apiario -> Colmeia -> Inspecao (observacao humana).
Colmeia -> SerieDataset -> Leitura (medicao historica do arquivo CSV).

O backend usa SQLAlchemy e PyMySQL. Os nomes, campos e relacionamentos seguem
esse SQL. A inicializacao da API nao cria, altera nem apaga tabelas.
GET /health confere conexao, nomes e colunas; os testes verificam o comportamento
no MySQL real, usando um schema temporario separado.

Leituras sao somente consulta na API. A importacao preserva a origem, o checksum,
a linha do CSV, o timestamp original e o texto numerico original. Horarios
repetidos e pesos negativos sao preservados. Unidade e fuso acompanham a serie.

A chave X-API-Key protege esta API administrativa local. Ela nao representa
a identidade de um apicultor. Os filtros usuario_id e apiario_id sao filtros
administrativos, nao controles de autorizacao individual. Nao ha login/JWT.
Os usuarios cadastrados possuem senha em hash scrypt, nunca retornada pela API.

Fora desta etapa: dispositivos, eventos de manejo, previsoes persistidas,
notificacoes, clima e consolidacao de semaforo. As anotacoes restantes em
motor/ descrevem trabalho futuro; nao geram diagnosticos nesta API.
