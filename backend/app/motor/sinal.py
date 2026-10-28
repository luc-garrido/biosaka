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
from datetime import datetime, timedelta
from typing import List, Optional

from .tipos import LeituraPura, FeaturesSinal

def limpar_leituras_invalidas(leituras):
   leituras_validas = []
   peso_min = 0.0
   peso_max = 150.0

   for leitura in leituras:
      if peso_min <= leitura.peso_kg <= peso_max:
         leituras_validas.append(leitura)
   return leituras_validas

def extrair_peso_noturno(leituras_validas, data_alvo: datetime, hora_inicio: int = 22, hora_fim: int = 4):
   pesos_noturnos = []
   fim_janela = datetime(data_alvo.year, data_alvo.month, data_alvo.day, hora_fim, 0)
   inicio_janela = datetime(data_alvo.year, data_alvo.month, data_alvo.day, hora_inicio, 0) - timedelta(days=1)
   
   for leitura in leituras_validas:
      if inicio_janela <= leitura.data_hora <= fim_janela:
         pesos_noturnos.append(leitura.peso_kg)
      else:
         continue
   if not pesos_noturnos:
      return None
   media_pesos = sum(pesos_noturnos)/len(pesos_noturnos)
   return round(media_pesos,2)


def detectar_queda_abrupta(leituras, janela_horas: int = 4, limiar_queda_kg: float = 1.5):
    if len(leituras) < 2:
        return False
        
    leituras_ordenadas = sorted(leituras, key=lambda l: l.data_hora)
    leitura_atual = leituras_ordenadas[-1]

    inicio_janela = leitura_atual.data_hora - timedelta(hours=janela_horas)
    leituras_janela = [l for l in leituras_ordenadas if l.data_hora >= inicio_janela]

    if len(leituras_janela) < 2:
        return False

    peso_maximo = max(l.peso_kg for l in leituras_janela)
    queda = peso_maximo - leitura_atual.peso_kg

    return queda >= limiar_queda_kg


def extrair_features_sinal(leituras, peso_tara_kg: float, data_referencia: datetime):
   leituras_validas = limpar_leituras_invalidas(leituras)

   peso_noturno = extrair_peso_noturno(leituras_validas, data_referencia)
   peso_base = peso_noturno if peso_noturno is not None else (leituras_validas[-1].peso_kg if leituras_validas else 0.0)
   peso_ontem = extrair_peso_noturno(leituras_validas, data_referencia - timedelta(days=1))
   delta_24h = round(peso_base - peso_ontem, 2) if (peso_base and peso_ontem) else 0.0

   peso_7d = extrair_peso_noturno(leituras_validas, data_referencia - timedelta(days=7))
   delta_7d = round(peso_base - peso_7d, 2) if (peso_base and peso_7d) else 0.0
   
   queda_abrupta = detectar_queda_abrupta(leituras_validas)
   reserva_liquida = round(max(0.0, peso_base - peso_tara_kg), 2)


   return FeaturesSinal(
      peso_noturno_atual=peso_base,
      delta_24h=delta_24h,
      delta_7d=delta_7d,
      queda_abrupta_detectada=queda_abrupta,
      reserva_liquida_alimento_kg=reserva_liquida
   )
