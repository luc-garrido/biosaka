"""
==============================================================================
ARQUIVO: app/motor/sinal.py
PAPEL: "O Lavador de Ingredientes / Limpador de Ruídos da Balança"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo contém funções matemáticas puras para pré-processar e limpar
os dados brutos que chegam da balança física do ESP32.

POR QUE ELE EXISTE SEPARADO?
Na vida real, a balança física que fica embaixo da colmeia no meio da roça
enfrenta muitos problemas:
1. O sol esquenta a estrutura de metal e ela dilata, alterando ligeiramente a medição.
2. O vento forte balança a caixa e gera picos falsos de peso.
3. Durante o dia, milhares de abelhas saem para voar e buscar néctar (forrageamento),
   fazendo o peso da colmeia oscilar o tempo todo.

Se tentássemos calcular se a colmeia está com fome olhando o peso do meio-dia,
o cálculo daria errado porque metade das abelhas estaria fora da caixa!

O QUE ESTE ARQUIVO FAZ NA PRÁTICA:
1. Limpeza de Outliers: joga fora leituras absurdas (ex: um peso de 500 kg que
   ocorreu por uma falha momentânea de sinal elétrico).
2. Filtro Noturno: isola as leituras feitas na madrugada (entre 22h e 04h).
   Nesse horário, todas as abelhas estão dormindo juntas dentro da caixa,
   o vento costuma ser calmo e não há luz solar direta. É o PESO REAL DA COLMEIA.
3. Cálculo de Derivadas (Tendências):
   - Variação em 2 a 4 horas: se cair 2 kg rápido, pode ser enxameação!
   - Variação em 24h, 3 dias e 7 dias: se cair devagarzinho todo dia, é consumo de fome.
     Se subir firme todo dia, é acúmulo de mel!
==============================================================================
"""
