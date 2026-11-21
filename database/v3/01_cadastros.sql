-- BIOSAKA - base de cadastros da terceira entrega.
-- MySQL 8.0.16+. Executar uma vez em schema NOVO e vazio.
-- Nao e migracao dos scripts anteriores; nao substituir um banco existente.
-- DDL no MySQL realiza commit implicito. Validar em desenvolvimento primeiro.
-- Datas de auditoria: a conexao deve usar UTC (SET time_zone = '+00:00').
-- Senhas: somente hashes produzidos pela API. Nenhuma credencial e criada aqui.

CREATE TABLE usuarios (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    telefone VARCHAR(16) NOT NULL COMMENT 'Formato internacional: + seguido de digitos; normalizado pela API',
    email VARCHAR(254) NULL,
    senha_hash VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_usuarios_telefone UNIQUE (telefone),
    CONSTRAINT uq_usuarios_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE apiarios (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario_id BIGINT UNSIGNED NOT NULL,
    nome VARCHAR(120) NOT NULL,
    localizacao VARCHAR(255) NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_apiarios_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE colmeias (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    apiario_id BIGINT UNSIGNED NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    data_instalacao DATE NULL,
    situacao ENUM('ativa', 'em_observacao', 'inativa') NOT NULL DEFAULT 'ativa',
    especie_abelha VARCHAR(80) NULL,
    origem_rainha VARCHAR(120) NULL,
    data_introducao_rainha DATE NULL,
    peso_tara_kg DECIMAL(10,3) NULL COMMENT 'Opcional: nao deduzir tara do peso bruto do dataset',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_colmeias_apiario_codigo UNIQUE (apiario_id, codigo),
    CONSTRAINT ck_colmeias_tara CHECK (peso_tara_kg IS NULL OR peso_tara_kg >= 0),
    CONSTRAINT fk_colmeias_apiario FOREIGN KEY (apiario_id)
        REFERENCES apiarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE inspecoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    colmeia_id BIGINT UNSIGNED NOT NULL,
    data_inspecao DATE NOT NULL,
    forca_enxame ENUM('fraca', 'media', 'forte', 'nao_avaliada') NOT NULL DEFAULT 'nao_avaliada',
    postura ENUM('observada', 'nao_observada', 'nao_avaliada') NOT NULL DEFAULT 'nao_avaliada',
    reserva_alimentar ENUM('baixa', 'adequada', 'nao_avaliada') NOT NULL DEFAULT 'nao_avaliada',
    observacoes VARCHAR(2000) NOT NULL DEFAULT '',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_inspecoes_colmeia_data (colmeia_id, data_inspecao, id),
    CONSTRAINT fk_inspecoes_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
