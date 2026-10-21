"""
==============================================================================
ARQUIVO: app/motor/tipos.py
PAPEL: "O Dicionário Oficial de Termos do Motor"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo define as "palavras oficiais" e as estruturas de dados imutáveis
que o motor biológico do Biosaka usa. Ele garante que todo o sistema fale
exatamente o mesmo idioma.

POR QUE ELE EXISTE SEPARADO?
Imagine que um arquivo escreva o semáforo como "Verde", outro escreva "VERDE"
e outro escreva "verde". Isso causaria erros difíceis de encontrar.
Ao criar um Enum (uma lista fechada de opções válidas), nós travamos as opções:
o semáforo SÓ PODE ser VERDE, AMARELO ou VERMELHO. Nada além disso é aceito.

O QUE VAI FICAR AQUI DENTRO:
1. Enums (Opções fixas):
   - Semaforo: VERDE, AMARELO, VERMELHO.
   - Confianca: ALTA, MEDIA, BAIXA (indica se os dados do sensor são confiáveis).
   - CodigoRegra: RF01 (Abertura), RF03 (Colheita), RF04 (Fome), RF05 (Enxameação).

2. Dataclasses (Caixas organizadoras de dados):
   - LeituraPura: guarda apenas peso, data e hora sem depender de banco de dados.
   - FeaturesSinal: guarda os dados já limpos (peso noturno, tendência de perda/ganho).
   - ContextoClima: guarda temperatura, vento e chuva daquele momento.
   - DiagnosticoFinal: o pacote completo que será devolvido com a cor e a frase.

REGRA DE OURO DESTE ARQUIVO (E DE TODA A PASTA MOTOR):
Aqui é código puramente matemático e lógico em Python puro.
NÃO importamos FastAPI, NÃO conectamos ao banco de dados e NÃO pegamos a hora
do computador com datetime.now(). Tudo o que o motor precisa calcular deve ser
recebido explicitamente por quem o chama.
==============================================================================
"""
