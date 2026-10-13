# Biosaka: Arquitetura e Guia dos Arquivos do Backend

Este documento mapeia a estrutura simplificada e modular do backend do **Biosaka**, explicando a responsabilidade de cada bloco e o que deve ser implementado em cada arquivo específico.

---

## 1. Visão Macro do Sistema

```text
                    ┌──────────────────────┐
                    │  API meteorológica   │
                    │  (Open-Meteo etc.)   │
                    └──────────┬───────────┘
                               │ clima por apiário
 ┌──────────────┐              ▼              ┌──────────────────────┐
 │  Balança     │  peso   ┌─────────┐ alertas │ Notificação proativa │
 │  ESP32       ├────────►│ BIOSAKA ├────────►│ (WhatsApp / SMS)     │
 │  (célula de  │         │ BACKEND │         └──────────────────────┘
 │   carga)     │         │         │ status
 └──────────────┘         │         │◄───────►┌──────────────────────┐
                          └─────────┘         │ App "Modo Avô"       │
                                              │ (semáforo + frases)  │
                                              └──────────────────────┘
```

### Quatro Fronteiras do Sistema
1. **Dispositivo (Entrada):** ESP32 / Célula de carga enviando peso autenticado com timestamp.
2. **Clima (Contexto):** Dados meteorológicos por apiário (temperatura, vento, chuva).
3. **Apicultor (Interação):** Consulta visual (semáforo + frase de ação) e registro de manejos.
4. **Notificação (Saída proativa):** Avisos críticos (ex: enxameação, fome).

---

## 2. Mapa dos Arquivos e Suas Responsabilidades

```text
backend/
├── pyproject.toml
├── ARQUITETURA.md
├── app/
│   ├── main.py            # FastAPI, inicialização, middlewares e roteamento
│   ├── config.py          # Variáveis de ambiente e limiares padrão
│   ├── banco.py           # Engine, sessão e modelos de tabelas (SQLAlchemy)
│   ├── schemas.py         # Contratos Pydantic de entrada e saída
│   ├── rotas.py           # Endpoints HTTP (leituras, colmeias, manejo, status)
│   ├── servicos.py        # Orquestrador (a "cola" entre API, banco, clima e motor)
│   ├── clima.py           # Cliente HTTP da API de clima + cache em memória
│   │
│   └── motor/             # PACOTE PURO (sem FastAPI, sem banco, sem relógio)
│       ├── tipos.py       # Dataclasses e Enums fundamentais
│       ├── sinal.py       # Limpeza de ruído e cálculo de features
│       ├── regras.py      # Implementação das regras (RF01, RF03, RF04, RF05)
│       └── semaforo.py    # Consolidador de regras e tradutor para "Modo Avô"
│
├── simulador.py           # Gerador de séries sintéticas para testes
└── tests/
    └── test_motor.py      # Testes unitários do motor puro
```

---

## 3. O que deve conter em cada arquivo

### Raiz do Backend

#### `backend/pyproject.toml`
- **Responsabilidade:** Gerenciamento de dependências e metadados do projeto Python.
- **Conteúdo esperado:**
  - Dependências principais: `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `httpx`.
  - Dependências de desenvolvimento/testes: `pytest`.
  - Configurações do interpretador e ferramentas de lint/teste.

#### `backend/simulador.py`
- **Responsabilidade:** Gerador de dados de teste (séries temporais sintéticas) simulando o comportamento real das colmeias.
- **Conteúdo esperado:**
  - Funções geradoras de curvas diárias de peso (com ruído térmico e forrageamento diário).
  - Cenários sintéticos para teste:
    - Queda abrupta sem manejo (enxameação).
    - Perda gradual contínua (fome / consumo de reserva).
    - Aumento sustentado contínuo (colheita pronta).
    - Degrau de peso positivo/negativo com marcação humana (manejo/inserção de melgueira).

---

### Camada de Aplicação (`backend/app/`)

#### `backend/app/main.py`
- **Responsabilidade:** Ponto de entrada da aplicação web FastAPI.
- **Conteúdo esperado:**
  - Instância do `FastAPI(title="Biosaka API", ...)`.
  - Configuração de middlewares (CORS para permitir o frontend).
  - Inclusão dos roteadores definidos em `rotas.py`.
  - Criação automática das tabelas do banco no ciclo de vida (startup/lifespan).

#### `backend/app/config.py`
- **Responsabilidade:** Centralização de configurações de ambiente e parâmetros de corte biológicos.
- **Conteúdo esperado:**
  - Configurações de ambiente (`DATABASE_URL`, chaves de API, níveis de log).
  - Limiares padrão de corte (fallback global caso a colmeia não possua calibração própria):
    - Limiar de fome crítica (ex: reserva < 3.0 kg).
    - Limiar de colheita pronta (ex: ganho > 15.0 kg).
    - Limiar de queda para enxameação (ex: queda > 1.5 kg em janela curta).
    - Limiares de clima seguro para abertura (temperatura mínima, ausência de chuva, vento máximo).

#### `backend/app/banco.py`
- **Responsabilidade:** Camada de persistência relacional com SQLAlchemy.
- **Conteúdo esperado:**
  - Criação do `engine`, `SessionLocal` e função utilitária `get_db()` para injeção de dependência.
  - Modelos ORM (tabelas):
    - `Apiario`: identificação, localização (latitude/longitude para o clima).
    - `Colmeia`: identificação, espécie, peso de tara atual, vínculo ao apiário.
    - `Leitura`: série temporal (colmeia_id, timestamp, peso_bruto, temperatura_sensor).
    - `EventoManejo`: histórico de ações humanas (tipo, colmeia_id, delta_peso_esperado, data_hora).
    - `Alerta`: registros de alertas gerados, nível de gravidade, flag de resolvido/reconhecido.
    - `EstadoAtual`: cache do último diagnóstico consolidado da colmeia (semáforo, frase, data da avaliação).

#### `backend/app/schemas.py`
- **Responsabilidade:** Contratos de dados e validação via Pydantic (DTOs).
- **Conteúdo esperado:**
  - **Entradas:**
    - `LeituraIn`: peso bruto, timestamp (obrigatório), temperatura do sensor.
    - `EventoManejoIn`: tipo de manejo (alimentação, colheita, troca de ninho), descrição, data_hora.
    - `ColmeiaIn` / `ApiarioIn`: criação e edição cadastral.
  - **Saídas:**
    - `StatusOut`: semáforo (VERDE, AMARELO, VERMELHO), frase no "Modo Avô", confiança, data do cálculo.
    - `ColmeiaOut`, `AlertaOut`, `LeituraOut`.

#### `backend/app/rotas.py`
- **Responsabilidade:** Controladores HTTP (endpoints da API).
- **Conteúdo esperado:**
  - `POST /leituras`: recebe leituras da balança ESP32.
  - `GET /colmeias` e `POST /colmeias`: listagem e cadastro de caixas.
  - `POST /colmeias/{id}/manejo`: apicultor registra intervenções no campo.
  - `GET /colmeias/{id}/status`: consulta o estado calculado mais recente ("Modo Avô").
  - `GET /colmeias/{id}/alertas`: histórico de alertas gerados.

#### `backend/app/servicos.py`
- **Responsabilidade:** A "cola" de orquestração do sistema (conecta HTTP, banco, clima e o motor puro).
- **Conteúdo esperado:**
  - `processar_nova_leitura(db, colmeia_id, leitura_in)`:
    1. Grava a leitura bruta no banco de dados.
    2. Busca o histórico recente de leituras e os eventos de manejo recentes.
    3. Obtém dados climáticos recentes do apiário via `clima.py`.
    4. Chama o processamento de sinal (`sinal.py`) para extrair peso noturno e tendências.
    5. Executa as regras de decisão (`regras.py`).
    6. Consolida o semáforo final e frase do "Modo Avô" (`semaforo.py`).
    7. Atualiza a tabela `EstadoAtual` e dispara notificações se um alerta for ativado.
  - `registrar_manejo(db, colmeia_id, evento_in)`:
    - Grava o evento e atualiza o histórico de calibração/tara da colmeia.

#### `backend/app/clima.py`
- **Responsabilidade:** Integração com serviços de meteorologia externa (ex: Open-Meteo) com estratégia de cache.
- **Conteúdo esperado:**
  - Cliente HTTP assíncrono (usando `httpx`).
  - Cache em memória com TTL (Time-To-Live, ex: 30 a 60 minutos) por coordenadas de apiário.
  - Tratamento de falha segura: se a API externa falhar, retorna dados marcados como indisponíveis/antigos para acionar o estado de incerteza (semáforo amarelo).

---

### Núcleo Puro: Motor de Decisão (`backend/app/motor/`)

> **REGRA DE OURO DO MOTOR:** Esta pasta é código puramente matemático e lógico. **Não importa FastAPI, não importa SQLAlchemy, não faz consultas de banco e não consulta o relógio do sistema (`datetime.now()`)**. Todas as datas e dados são recebidos explicitamente como parâmetros.

#### `backend/app/motor/tipos.py`
- **Responsabilidade:** Tipagem estrita, Enums e Dataclasses imutáveis do motor.
- **Conteúdo esperado:**
  - `Semaforo` (Enum: `VERDE`, `AMARELO`, `VERMELHO`).
  - `Confianca` (Enum: `ALTA`, `MEDIA`, `BAIXA`).
  - `CodigoRegra` (Enum: `RF01`, `RF03`, `RF04`, `RF05`).
  - Dataclasses:
    - `LeituraPura(timestamp, peso, temperatura)`.
    - `FeaturesSinal(peso_noturno_atual, delta_24h, tendencia_7d, ruido_alto)`.
    - `ContextoClima(temperatura, chuva_recente, vento_kmh, dados_confiaveis)`.
    - `ResultadoRegra(codigo, nivel, acao_sugerida, confianca, motivo)`.
    - `DiagnosticoFinal(semaforo, frase_modo_avo, detalhes, confianca)`.

#### `backend/app/motor/sinal.py`
- **Responsabilidade:** Pré-processamento e filtragem da série temporal de peso.
- **Conteúdo esperado:**
  - Limpeza de ruído e descarte de leituras espúrias.
  - Filtro de peso noturno (amostras colhidas entre 22h e 04h, quando as campeiras estão dentro da colmeia e o peso é representativo).
  - Cálculo de grandezas derivadas:
    - Derivada rápida (variação em 2 a 4 horas).
    - Tendência acumulada (variação em 24h, 3 dias, 7 dias).

#### `backend/app/motor/regras.py`
- **Responsabilidade:** As 4 regras de negócio do Biosaka implementadas como funções puras.
- **Conteúdo esperado:**
  - **RF01 - Abertura Segura de Caixa:**
    - Avalia condições meteorológicas para manejo sem matar crias nem irritar o enxame (temperatura > 18°C, sem chuva, vento ameno).
  - **RF03 - Ponto de Colheita de Mel:**
    - Avalia se o ganho de peso acumulado atingiu o patamar esperado de melgueira cheia e estabilizou (sugerindo mel operculado).
  - **RF04 - Fome e Esgotamento de Reservas:**
    - Detecta quando a reserva de alimento cai abaixo do limite crítico (< 3 kg) ou sofre queda contínua no período de entressafra.
  - **RF05 - Alerta de Enxameação:**
    - Detecta queda brusca de peso (ex: 1.5 a 3.0 kg perdidos em poucas horas) **sem** que haja um registro de manejo humano correspondente.

#### `backend/app/motor/semaforo.py`
- **Responsabilidade:** Consolidação das saídas das regras e tradução para a linguagem humana do "Modo Avô".
- **Conteúdo esperado:**
  - Algoritmo de prioridade: `VERMELHO` prevalece sobre `AMARELO`, que prevalece sobre `VERDE` (ex: emergência de fome ou enxameação anula aviso de colheita).
  - Regra de falha segura: falta de dados meteorológicos ou de leituras rebaixa para `AMARELO`.
  - Mapeamento código → Frases simples e sem jargões para o apicultor:
    - *Exemplo RF04:* "Suas abelhas estão sem comida! Alimente com xarope imediatamente."
    - *Exemplo RF05:* "Possível enxameação: a caixa perdeu peso de repente."
    - *Exemplo RF03:* "Hora da colheita! A melgueira está cheia."
    - *Exemplo RF01:* "Dia favorável para abrir a caixa e fazer revisão."

---

### Testes Automatizados (`backend/tests/`)

#### `backend/tests/test_motor.py`
- **Responsabilidade:** Bateria de testes unitários isolados do motor usando `pytest`.
- **Conteúdo esperado:**
  - Testes com séries sintéticas geradas pelo `simulador.py`.
  - Cenários de teste:
    1. Teste de enxameação acionada por degrau de queda.
    2. Teste de anulação de alerta de enxameação quando há evento de colheita humana registrado.
    3. Teste de fome progressiva ativando semáforo vermelho.
    4. Teste de colheita pronta com estabilização de peso.
    5. Teste de bloqueio de abertura em dias frios ou chuvosos (RF01).
    6. Teste de falha segura (dados ausentes resultando em amarelo).
