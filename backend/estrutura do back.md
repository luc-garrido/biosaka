biosaka/
├── pyproject.toml
├── .env.example
├── alembic.ini
├── migrations/                    # versões do esquema do banco
│
├── app/
│   ├── main.py                    # cria o FastAPI, registra routers e agendador
│   │
│   ├── config/
│   │   ├── settings.py            # variáveis de ambiente (Pydantic Settings)
│   │   └── limiares.py            # padrões globais: 3 kg, 15 kg, janelas horárias etc.
│   │
│   ├── api/                       # única camada que conhece HTTP
│   │   ├── deps.py                # dependências: sessão do banco, auth do dispositivo
│   │   ├── schemas/
│   │   │   ├── entrada.py         # LeituraIn, EventoManejoIn
│   │   │   └── saida.py           # StatusOut, ColmeiaOut, AlertaOut
│   │   ├── entrada/
│   │   │   ├── leituras.py        # POST /leituras (ESP32)
│   │   │   └── manejo.py          # POST /colmeias/{id}/manejo
│   │   └── saida/
│   │       ├── status.py          # GET /colmeias/{id}/status
│   │       ├── colmeias.py        # CRUD de colmeias
│   │       ├── apiarios.py        # CRUD de apiários
│   │       ├── alertas.py         # histórico e reconhecimento
│   │       ├── nutricao.py        # GET /nutricao/calculadora
│   │       └── apresentacao.py    # código da regra → frase do "Modo Avô"
│   │
│   ├── dominio/                   # núcleo: sem FastAPI, sem banco, sem relógio
│   │   ├── entidades.py           # Apiario, Colmeia, Leitura, EventoManejo, Alerta
│   │   ├── enums.py               # Semaforo, Confianca, TipoManejo, CodigoRegra
│   │   └── resultado.py           # ResultadoRegra (nível, código, confiança)
│   │
│   ├── sinal/                     # pré-processamento (funções puras)
│   │   ├── limpeza.py             # outliers, mediana móvel
│   │   ├── compensacao.py         # compensação de temperatura
│   │   ├── janelas.py             # recortes por período e exclusão de janelas de manejo
│   │   └── features.py            # peso noturno, tendência, derivada
│   │
│   ├── decisao/                   # regras puras
│   │   ├── base.py                # Protocol Regra: avaliar(features, contexto)
│   │   ├── enxameacao.py          # RF05
│   │   ├── fome.py                # RF04
│   │   ├── colheita.py            # RF03
│   │   ├── abertura.py            # RF01
│   │   └── consolidador.py        # prioridade e semáforo final
│   │
│   ├── servicos/                  # orquestra: busca dados, chama sinal/decisao, persiste
│   │   ├── ingestao.py            # valida, deduplica, grava, dispara avaliação
│   │   ├── avaliacao.py           # pipeline: sinal → regras → consolidador → estado
│   │   ├── manejo.py              # registra evento e recalibra tara
│   │   ├── clima.py               # cliente da API meteorológica + cache
│   │   ├── notificacao.py         # WhatsApp/SMS (atrás de uma interface)
│   │   └── nutricao.py            # fórmulas de xarope e pasta proteica
│   │
│   ├── persistencia/
│   │   ├── banco.py               # engine e sessão
│   │   ├── modelos.py             # tabelas (SQLAlchemy)
│   │   └── repositorios/
│   │       ├── colmeias.py
│   │       ├── leituras.py
│   │       ├── manejo.py
│   │       ├── alertas.py
│   │       ├── clima.py
│   │       └── estado.py
│   │
│   ├── seguranca/
│   │   └── dispositivo.py         # chave de API do ESP32 (hash, verificação)
│   │
│   └── tarefas/
│       └── agendador.py           # clima periódico e avaliações baseadas em tempo
│
├── simulador/                     # fora de app/: não vai para produção
│   ├── gerador.py                 # ciclo diário, ruído, deriva
│   └── cenarios.py                # enxameação, fome, colheita, manejo humano
│
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── sinal/
    │   └── decisao/               # regras testadas com séries do simulador
    └── integracao/                # rotas + banco de teste
