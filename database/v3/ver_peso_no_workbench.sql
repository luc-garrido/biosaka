-- Executar conectado ao MySQL local: host 127.0.0.1, porta 3307.
USE biosaka_v3_dev;

-- Origem, unidade e identificacao da colmeia de demonstracao.
SELECT c.id AS colmeia_id, c.codigo AS colmeia, s.id AS serie_id,
       s.codigo AS serie, s.arquivo_origem, s.unidade_original,
       s.fuso_original, s.sha256_arquivo
FROM series_dataset s
JOIN colmeias c ON c.id=s.colmeia_id
WHERE s.codigo='beehive-metrics-v3-wurzburg-weight-2017';

-- Quantidade e periodo. Pesos negativos ficam visiveis para revisao.
SELECT COUNT(*) AS total_leituras,
       MIN(l.instante_original) AS inicio,
       MAX(l.instante_original) AS fim,
       SUM(l.valor_original<0) AS pesos_negativos,
       SUM(l.valor_original IS NULL) AS valores_ausentes
FROM leituras l
JOIN series_dataset s ON s.id=l.serie_id
WHERE s.codigo='beehive-metrics-v3-wurzburg-weight-2017';

-- Primeiras 20 medicoes; horarios originais sem conversao presumida de fuso.
SELECT l.linha_origem, l.instante_original, l.valor_original AS peso_kg,
       l.texto_valor_original,
       CASE WHEN l.valor_original IS NULL THEN 'ausente'
            WHEN l.valor_original<0 THEN 'revisar: peso negativo'
            ELSE 'sem indicacao de peso negativo' END AS verificacao_basica
FROM leituras l
JOIN series_dataset s ON s.id=l.serie_id
WHERE s.codigo='beehive-metrics-v3-wurzburg-weight-2017'
ORDER BY l.linha_origem
LIMIT 20;

-- Exemplo dos horarios repetidos: manter ambas as linhas.
SELECT l.linha_origem, l.instante_original, l.valor_original AS peso_kg
FROM leituras l
JOIN series_dataset s ON s.id=l.serie_id
WHERE s.codigo='beehive-metrics-v3-wurzburg-weight-2017'
  AND l.instante_original BETWEEN '2017-10-29 02:00:00' AND '2017-10-29 02:02:00'
ORDER BY l.instante_original,l.linha_origem;
