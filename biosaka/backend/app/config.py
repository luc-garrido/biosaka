"""
==============================================================================
ARQUIVO: app/config.py
PAPEL: "O Painel de Controle / Central de Configurações e Limiares"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo centraliza todos os parâmetros que podem mudar conforme o ambiente
(desenvolvimento no seu computador vs produção na nuvem) e os números biológicos
padrão do sistema.

POR QUE ELE EXISTE SEPARADO?
Nunca devemos espalhar senhas de banco ou valores como "3.0 kg de fome" soltos
no meio do código.
- Se a senha do MySQL mudar, você só altera em um arquivo '.env'.
- Se um biólogo disser que agora o limite de fome não é 3.0 kg, mas 3.5 kg, você
  muda em uma única variável aqui, e todo o sistema se atualiza automaticamente!

O QUE VAI FICAR AQUI DENTRO:
1. Variáveis de Ambiente (Segredos e Conexões):
   - DATABASE_URL: o endereço e login do MySQL.
   - PORTA: a porta onde o servidor vai rodar.
   - NÍVEL DE LOG: se queremos mensagens detalhadas no terminal para depuração.

2. Limiares Biológicos Padrão (Fallback Global):
   - LIMIAR_FOME_CRITICA_KG = 3.0  (abaixo disso = alerta vermelho de fome)
   - LIMIAR_COLHEITA_PRONTA_KG = 15.0 (ganho acumulado esperado de uma melgueira cheia)
   - LIMIAR_QUEDA_ENXAMEACAO_KG = 1.5 (perda rápida em poucas horas que indica fuga)
   - CLIMA_TEMP_MINIMA_ABERTURA = 18.0 (temperatura mínima segura para abrir a tampa)
   - CLIMA_VENTO_MAXIMO_KMH = 30.0 (vento máximo tolerável para mexer no apiário)
==============================================================================
"""
