CREATE DATABASE IF NOT EXISTS biosaka_db;
USE biosaka_db;

-- 1. TABELA DE USUÁRIOS (APICULTORES)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELA DE APIÁRIOS (LOCAIS / PROPRIEDADES)
CREATE TABLE IF NOT EXISTS apiarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    localizacao VARCHAR(200),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_apiario_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 3. TABELA DE COLMEIAS (CAIXAS INDIVIDUAIS)
CREATE TABLE IF NOT EXISTS colmeias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apiario_id INT NOT NULL,
    codigo_identificacao VARCHAR(20) NOT NULL,
    especie_abelha VARCHAR(80),
    data_instalacao DATE NOT NULL,
    status ENUM('ATIVA', 'EM_OBSERVACAO', 'INATIVA') DEFAULT 'ATIVA',
    CONSTRAINT fk_colmeia_apiario FOREIGN KEY (apiario_id) REFERENCES apiarios(id) ON DELETE CASCADE
);

-- 4. TABELA DE INSPEÇÕES (REGISTRO DE CAMPO E SÉRIES TEMPORAIS)
CREATE TABLE IF NOT EXISTS inspecoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    data_inspecao DATETIME NOT NULL,
    peso_kg DECIMAL(5,2) NOT NULL,
    presenca_rainha BOOLEAN DEFAULT TRUE,
    nivel_populacao ENUM('BAIXO', 'MEDIO', 'ALTO') DEFAULT 'ALTO',
    reserva_alimento ENUM('CRITICA', 'SUFICIENTE', 'ABUNDANTE') DEFAULT 'SUFICIENTE',
    sinais_pragas BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    CONSTRAINT fk_inspecao_colmeia FOREIGN KEY (colmeia_id) REFERENCES colmeias(id) ON DELETE CASCADE
);

-- 5. TABELA DE ALERTAS PREDITIVOS E DE MANEJO
CREATE TABLE IF NOT EXISTS alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    tipo_alerta ENUM('COLHEITA_PRONTA', 'QUEDA_PESO_ENXAMEACAO', 'ALIMENTACAO_URGENTE', 'PRAGA_DETECTADA') NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    gravidade ENUM('BAIXA', 'MEDIA', 'ALTA') DEFAULT 'MEDIA',
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolvido BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_alerta_colmeia FOREIGN KEY (colmeia_id) REFERENCES colmeias(id) ON DELETE CASCADE
);

-- Lucas e Henrique, verifiquem se é isso que eu preciso fazer: 

CREATE TABLE IF NOT EXISTS leituras_peso (
   id INT AUTO_INCREMENT PRIMARY KEY,
   colmeia_id INT NOT NULL,
   peso_kg DECIMAL(5,2) NOT NULL,
   data_leitura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   CONSTRAINT fk_leitura_colmeia FOREIGN KEY (colmeia_id)
       REFERENCES colmeias(id)
       ON DELETE CASCADE
       ON UPDATE CASCADE,
   INDEX idx_leitura_colmeia_data (colmeia_id, data_leitura)
 );



/*OBSERVAÇÕES

Dados sobre o que existe dentro da colmeia devem pertencer a tabela COLMEIA, exemplo: Peso, rainha, população, etc. 

A tabela INSPEÇÕES deve conter resultados do nosso back, exemplo: Colheita (true ou false) que se baseia nas informações da colmeia + data da colheita.
Saude da colmeia que é um resultado do back em uma condicional entre inforamções base da tabela colmeia, etc.

Montar um arquivo no molde de ARQUITETURA.md que descreva todas as tabelas, colunas, etc. Pense que precisa ser facil de interpretar o que tem no dataset
mesmo sem saber nada de código ou de banco de dados. */
