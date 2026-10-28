CREATE DATABASE IF NOT EXISTS biosaka_db;
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; -- o utf8mb4 faz aceitar quase td q a pessoa digitar e o collate + ci faz com que ele não diferencie A de a.
USE biosaka_db;

/* Vale lembrar que qualquer coisa relacionada a temperatura está aqui para facilitar a implantação no futuro, já que não queremos mexer com sensor térmico
nesse momento. */
--------------------------------------------------------------------------------------------------------

-- 1 ENDEREÇOS (reaproveitado por usuários e apiários)
CREATE TABLE IF NOT EXISTS enderecos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(60) NOT NULL,
    pais VARCHAR(60) NOT NULL DEFAULT 'Brasil' -- se o país não for informado, assume Brasil.
);
/* Serve para guardar cidade, estado e país. Fica em uma tabela própria, e não como colunas soltas, para que usuários e apiários usem o mesmo formato 
   sem repetir estrutura. */ 
--------------------------------------------------------------------------------------------------------

-- 2 USUÁRIOS (cliente)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE, -- impede dois cadastros com o mesmo e-mail com unique.
    senha_hash VARCHAR(255) NOT NULL, -- guarda a senha já criptografada, não em txt basico.
    telefone VARCHAR(20) NULL,
    endereco_id INT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_endereco FOREIGN KEY (endereco_id)
        REFERENCES enderecos(id) ON DELETE SET NULL
);
 -- Representa cada cliente do sistema.
--------------------------------------------------------------------------------------------------------

-- 3 APIÁRIOS (localizaçaõ das caixas)
CREATE TABLE IF NOT EXISTS apiarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    endereco_id INT NULL,
    referencia_local VARCHAR(200) NULL,      -- referencia do endereço, ex:"sitio Boa Vista, perto do corrego"
    latitude DECIMAL(9,6) NULL,              -- altitude durr (se tiver saco para descobrir)
    longitude DECIMAL(9,6) NULL,             -- same para longitude ^
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_apiario_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id) ON DELETE CASCADE, -- apaga o apiario se o usuario for apagado
    CONSTRAINT fk_apiario_endereco FOREIGN KEY (endereco_id)
        REFERENCES enderecos(id) ON DELETE SET NULL
);
/* O endereço fica aqui, e não na colmeia, porque todas as colmeias de um apiário X estão no mesmo lugar.
   "latitude" e "longitude": opcionais, servem para cruzar com dados de clima. esta em DECIMAL(9,6) onde é um número com até 9 dígitos, sendo 6 depois 
   da vírgula, servindo para coordenadas. */
--------------------------------------------------------------------------------------------------------

-- 4 ESPÉCIES (lista de opções de espécies que apareceram pro cliente ao cadastrar a caixa)
CREATE TABLE IF NOT EXISTS especies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL UNIQUE,
    nome_cientifico VARCHAR(120) NULL,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,    --  permite cadastrar uma espécie antes de liberá-la no site, onde "false = ainda não aparece como opção".
    observacoes TEXT NULL
);
/* Lista das espécies de abelha cadastradas, evitando redundancia. O cliente escolhe uma opção e todas as colmeias da mesma espécie ficam ligadas 
   ao mesmo registro. Isso prepara o sys para ter regras específicas por espécie no futuro (se formos vender essa bomba). */
--------------------------------------------------------------------------------------------------------

-- 5 COLMEIAS (dados fixos/estaveis)
CREATE TABLE IF NOT EXISTS colmeias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apiario_id INT NOT NULL,
    especie_id INT NOT NULL,
    codigo_identificacao VARCHAR(20) NOT NULL,
    data_instalacao DATE NOT NULL,
    status ENUM('ATIVA', 'EM_OBSERVACAO', 'INATIVA') NOT NULL DEFAULT 'ATIVA',
    peso_vazio_kg DECIMAL(6,2) NULL,         -- caixa sem abelhas nem reservas para servir de tara
    capacidade_max_kg DECIMAL(6,2) NULL,     -- peso total em que a caixa é considerada cheia para os alertas
    CONSTRAINT uq_colmeia_codigo UNIQUE (apiario_id, codigo_identificacao), -- evitar repetir codigos dentro do mesmo apiário
    CONSTRAINT fk_colmeia_apiario FOREIGN KEY (apiario_id)
        REFERENCES apiarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_colmeia_especie FOREIGN KEY (especie_id)
        REFERENCES especies(id)
);
/* Cada caixa individual, guardando só dados que mudam pouco (quase fixos ou sem histórico necessário).
   "ENUM": o campo só aceita um dos valores listados. */
--------------------------------------------------------------------------------------------------------

-- 6 DISPOSITIVOS (tabela pro arduno e balança)
CREATE TABLE IF NOT EXISTS dispositivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    identificador_hardware VARCHAR(50) NOT NULL UNIQUE,
    fator_calibracao DECIMAL(12,6) NULL,          -- número usado para converter a leitura bruta da balança em kg
    data_instalacao DATE NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    ultima_comunicacao DATETIME NULL,        -- permite identificar aparelhos que pararam de enviar dados.
    CONSTRAINT fk_dispositivo_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE
);
-- Existe para o sistema detectar balança off, aparelho trocado ou calibração errada.
--------------------------------------------------------------------------------------------------------

-- 7 LEITURAS DE PESO (dados do peso brutos)
CREATE TABLE IF NOT EXISTS leituras_peso (
    id BIGINT AUTO_INCREMENT PRIMARY KEY, --bigint, BIG INT tendeu (varias leituras no dia, tabela enorme)
    colmeia_id INT NOT NULL,
    dispositivo_id INT NULL,
    peso_kg DECIMAL(6,2) NOT NULL,
    data_leitura DATETIME NOT NULL,                       -- quando o sensor mediu
    data_recebimento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- quando o servidor recebeu
    bateria_v DECIMAL(4,2) NULL,                 -- avisa se a bateria ta morrendo
    temperatura_c DECIMAL(4,1) NULL,
    umidade_pct DECIMAL(4,1) NULL,
    valida BOOLEAN NOT NULL DEFAULT TRUE,                 -- falso = leitura descartada nas análises (ex: defeito)
    CONSTRAINT uq_leitura_colmeia_data UNIQUE (colmeia_id, data_leitura),  -- evita duplicar leitura da mesma caixa se ler 2x
    CONSTRAINT fk_leitura_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE,
    CONSTRAINT fk_leitura_dispositivo FOREIGN KEY (dispositivo_id)
        REFERENCES dispositivos(id) ON DELETE SET NULL -- se o aparelho for removido, as leituras antigas continuam guardadas. 
);
/* Tabela principal do sistema, cada linha é uma medida da balança. 
   "data_leitura" e "data_recebimento": o primeiro é quando a balança mediu e o segundo é quando o servidor recebeu. Como o envio será em lote, os dois horários 
   são diferentes, e as análises devem usar "data_leitura". */
--------------------------------------------------------------------------------------------------------

-- 8 PESO DIÁRIO (resumo calculado pro sys n ter q calcular td)
CREATE TABLE IF NOT EXISTS peso_diario (
    colmeia_id INT NOT NULL,
    data_referencia DATE NOT NULL,
    peso_medio_kg DECIMAL(6,2) NOT NULL,
    peso_minimo_kg DECIMAL(6,2) NOT NULL,
    peso_maximo_kg DECIMAL(6,2) NOT NULL,
    peso_noturno_kg DECIMAL(6,2) NULL,  -- peso de quando tds as abelhas estão na caixa
    qtd_leituras INT NOT NULL,
    PRIMARY KEY (colmeia_id, data_referencia),
    CONSTRAINT fk_pesodiario_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE
);
/* Como o poder de processamento é limitado, o sistema consulta este resumo em vez de reler milhares de leituras brutas sempre que for fazer uma análise.
   peso noturno é o mais estável e serve de base para medir tendências.
   "PRIMARY KEY (colmeia_id, data_referencia)", a chave é formada por dois campos juntos, o que garante uma única linha por colmeia por dia. */
--------------------------------------------------------------------------------------------------------

-- 9 EVENTOS (o que foi feito pelo apicultor)
CREATE TABLE IF NOT EXISTS eventos_manejo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    tipo ENUM('COLHEITA', 'ALIMENTACAO', 'ADICAO_MELGUEIRA', 'REMOCAO_MELGUEIRA',
              'TROCA_CAIXA', 'DIVISAO', 'OUTRO') NOT NULL,
    data_evento DATETIME NOT NULL,
    variacao_peso_esperada_kg DECIMAL(6,2) NULL, 
    observacoes TEXT NULL,
    CONSTRAINT fk_evento_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE
);
/* Registra ações do cliente na caixa (colher, alimentar, adicionar melgueira...). Essas ações mudam o peso de repente, e sem esse registro o sistema
   confundiria uma colheita com uma enxameação ou invasão.
   "variacao_peso_esperada_kg" quanto o peso deve mudar por causa da ação (positivo ao alimentar, negativo ao colher). Permite ao sistema descontar o salto. */
--------------------------------------------------------------------------------------------------------

-- 10 INSPEÇÕES (validação do sistema)
CREATE TABLE IF NOT EXISTS inspecoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    data_inspecao DATETIME NOT NULL,
    presenca_rainha BOOLEAN NULL,                              -- null = não observado
    nivel_populacao ENUM('BAIXO', 'MEDIO', 'ALTO') NULL,
    reserva_alimento ENUM('CRITICA', 'SUFICIENTE', 'ABUNDANTE') NULL,
    sinais_pragas BOOLEAN NULL,
    observacoes TEXT NULL,
    CONSTRAINT fk_inspecao_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE
);
CREATE INDEX idx_inspecao_colmeia_data ON inspecoes (colmeia_id, data_inspecao);
/* Opcional, já que o objetivo do sistema é evitar isso, mas é o que permite descobrir se as previsões estão certas.
   Campos com "NULL", o vazio significa que não abriram. Os valores padrão antigos.
   "CREATE INDEX": cria um índice, que funciona como o índice de um livro, evitando varrer toda a tabela. */
--------------------------------------------------------------------------------------------------------

-- 11 PREVISÕES (resultados + janela de calendario de operação)
CREATE TABLE IF NOT EXISTS previsoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    especie_id INT NOT NULL,                  -- espécie cujas regras foram usadas
    tipo VARCHAR(50) NOT NULL,                -- ver lista no ARQUITETURA.md
    resultado VARCHAR(100) NOT NULL,          -- ex: ALIMENTAR, AGUARDAR, COLHER
    valor_estimado DECIMAL(10,2) NULL,        -- ex: população estimada, kg de mel
    unidade_valor VARCHAR(20) NULL,           -- ex: kg, abelhas
    janela_inicio DATETIME NOT NULL,
    janela_fim DATETIME NOT NULL,
    confianca DECIMAL(5,2) NOT NULL,          -- 0 a 100
    estimativa_inicial BOOLEAN NOT NULL DEFAULT TRUE,   -- verdadeiro até a regra ser calibrada com inspeções
    versao_modelo VARCHAR(30) NOT NULL,
    data_geracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inspecao_validacao_id INT NULL,           -- inspeção que confirmou ou negou a previsão
    acertou BOOLEAN NULL,                     -- null = ainda não validada
    CONSTRAINT chk_previsao_janela CHECK (janela_fim >= janela_inicio),
    CONSTRAINT chk_previsao_confianca CHECK (confianca BETWEEN 0 AND 100),
    CONSTRAINT fk_previsao_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE,
    CONSTRAINT fk_previsao_especie FOREIGN KEY (especie_id)
        REFERENCES especies(id),
    CONSTRAINT fk_previsao_inspecao FOREIGN KEY (inspecao_validacao_id)
        REFERENCES inspecoes(id) ON DELETE SET NULL
);
CREATE INDEX idx_previsao_colmeia_data ON previsoes (colmeia_id, data_geracao);
/* Guarda tudo o que o sistema conclui a partir do peso: necessidade de alimentação, colheita, população, caixa cheia, risco de enxameação, declínio suspeito.
   "tipo" e "resultado" são textos controlados pelo back-end para que cada espécie que futuramente for colocada no DS possa ter tipos próprios sem alterar o banco.
   "versao_modelo" e "especie_id": registram qual regra gerou a previsão, para compara versões e espécies depois.
   "inspecao_validacao_id" e "acertou": quando uma inspeção confirma ou contradiz a previsão, os dois campos registram isso. É a base para calibrar as regras.
   "CHECK": regra que o banco confere a cada gravação. Aqui impede uma janela que termina antes de começar e uma confiança fora de 0 a 100. Se usar versões anteriores ao 
   MySQL 8.0.16 vai ser é ignorado. */
--------------------------------------------------------------------------------------------------------

-- 12 ALERTAS (avisos baseados nas analises ou condição do hardware)
CREATE TABLE IF NOT EXISTS alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colmeia_id INT NOT NULL,
    previsao_id INT NULL,                     -- null em alertas de hardware (bateria, sensor)
    tipo_alerta VARCHAR(50) NOT NULL,         -- ver lista no ARQUITETURA.md
    descricao VARCHAR(255) NOT NULL,
    gravidade ENUM('BAIXA', 'MEDIA', 'ALTA') NOT NULL DEFAULT 'MEDIA',
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido BOOLEAN NOT NULL DEFAULT FALSE,
    data_resolucao DATETIME NULL,
    CONSTRAINT fk_alerta_colmeia FOREIGN KEY (colmeia_id)
        REFERENCES colmeias(id) ON DELETE CASCADE,
    CONSTRAINT fk_alerta_previsao FOREIGN KEY (previsao_id)
        REFERENCES previsoes(id) ON DELETE SET NULL
);
CREATE INDEX idx_alerta_colmeia_resolvido ON alertas (colmeia_id, resolvido);
-- A tabela é criada depois de "previsoes" porque depende dela, já que uma tabela só pode apontar para outra que já existe. 
