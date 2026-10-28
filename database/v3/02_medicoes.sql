-- Complemento de 01_cadastros.sql: guarda medicoes historicas e sua origem.
-- Baseada nos cabecalhos dos CSVs baixados; executada no MySQL 8.4 em Docker.
-- Integridade e importacao de weight_2017.csv validadas em 13/10/2026.
-- Valores e timestamps originais sao preservados sem presumir unidade/fuso.
-- Uma serie identifica UMA metrica de UMA colmeia em UMA fonte selecionada.

CREATE TABLE series_dataset (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    colmeia_id BIGINT UNSIGNED NOT NULL,
    codigo VARCHAR(100) NOT NULL,
    metrica ENUM('weight', 'temperature', 'humidity', 'flow') NOT NULL,
    fonte_url VARCHAR(500) NOT NULL,
    arquivo_origem VARCHAR(255) NOT NULL,
    sha256_arquivo CHAR(64) NOT NULL,
    unidade_original VARCHAR(40) NULL COMMENT 'NULL enquanto nao confirmada na fonte',
    fuso_original VARCHAR(64) NULL COMMENT 'NULL enquanto nao confirmado na fonte',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_series_codigo UNIQUE (codigo),
    CONSTRAINT fk_series_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE leituras (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    serie_id BIGINT UNSIGNED NOT NULL,
    instante_original DATETIME NOT NULL COMMENT 'Data/hora do CSV, sem conversao de fuso presumida',
    valor_original DECIMAL(24,12) NULL COMMENT 'Ausencia fica NULL; nunca substituir por zero',
    texto_valor_original VARCHAR(100) NULL COMMENT 'Valor textual preservado para rastreabilidade',
    linha_origem INT UNSIGNED NOT NULL COMMENT 'Numero da linha no CSV, incluindo cabecalho',
    importado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_leituras_serie_linha UNIQUE (serie_id, linha_origem),
    INDEX idx_leituras_serie_instante (serie_id, instante_original, id),
    CONSTRAINT ck_leituras_linha CHECK (linha_origem >= 2),
    CONSTRAINT fk_leituras_serie FOREIGN KEY (serie_id)
        REFERENCES series_dataset (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- O importador deve reutilizar a serie ao reimportar o MESMO arquivo/checksum.
-- Se o conteudo mudar, bloquear e exigir revisao: nao anexar nova versao como
-- se fossem leituras adicionais da mesma serie. Linha unica evita duplicar a
-- importacao e permite guardar timestamps repetidos existentes no original.
-- CSVs 2017 e CSVs por local nao devem ser unidos sem investigar sobreposicao.
