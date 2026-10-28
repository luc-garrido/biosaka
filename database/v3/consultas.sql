-- Consultas de inspecao, apos selecionar biosaka_v3_dev.
SHOW TABLES;

SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME;

SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, COLUMN_NAME;

-- Substituir IDs e datas conforme a serie importada. O filtro por usuario
-- deve vir da identidade autenticada na API, nao de um ID enviado pelo cliente.
SELECT s.codigo, s.metrica, s.unidade_original, s.fuso_original,
       COUNT(l.id) AS quantidade, MIN(l.instante_original) AS inicio,
       MAX(l.instante_original) AS fim
FROM series_dataset s
LEFT JOIN leituras l ON l.serie_id = s.id
GROUP BY s.id, s.codigo, s.metrica, s.unidade_original, s.fuso_original;
