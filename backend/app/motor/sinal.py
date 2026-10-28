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

def limpar_leituras_invalidas(leituras: List[LeituraPura]) -> List[LeituraPura]:
    leituras_validas = []
    peso_min = 0.0
    peso_max = 150.0

    for leitura in leituras:
        if peso_min <= leitura.peso_kg <= peso_max:
            leituras_validas.append(leitura)
    leituras_validas.sort(key=lambda l: l.data_hora)
    return leituras_validas

def extrair_peso_noturno(
    leituras_validas: List[LeituraPura],
    data_alvo: datetime,
    hora_inicio: int = 22,
    hora_fim: int = 4
) -> Optional[float]:
    # Se o horário do alvo já passou das 22h, a noite começou hoje e termina amanhã às 04h.
    # Caso contrário, a noite de referência começou ontem às 22h e terminou hoje às 04h.
    if data_alvo.hour >= hora_inicio:
        inicio_janela = datetime(data_alvo.year, data_alvo.month, data_alvo.day, hora_inicio, 0)
        fim_janela = (inicio_janela + timedelta(days=1)).replace(hour=hora_fim, minute=0)
    else:
        fim_janela = datetime(data_alvo.year, data_alvo.month, data_alvo.day, hora_fim, 0)
        inicio_janela = (fim_janela - timedelta(days=1)).replace(hour=hora_inicio, minute=0)
    
    pesos_noturnos = [
        leitura.peso_kg
        for leitura in leituras_validas
        if inicio_janela <= leitura.data_hora <= fim_janela
    ]

    if not pesos_noturnos:
        return None
    media_pesos = sum(pesos_noturnos) / len(pesos_noturnos)
    return round(media_pesos, 2)


def detectar_queda_abrupta(
    leituras: List[LeituraPura],
    janela_horas: int = 4,
    limiar_queda_kg: float = 1.5
) -> bool:
    if len(leituras) < 2:
        return False
        
    leituras_ordenadas = sorted(leituras, key=lambda l: l.data_hora)
    leitura_atual = leituras_ordenadas[-1]

    # Avaliamos o histórico recente (ex: últimas 24h) para não perder enxameações ocorridas há poucas horas
    limite_historico = leitura_atual.data_hora - timedelta(hours=24)
    leituras_recentes = [l for l in leituras_ordenadas if l.data_hora >= limite_historico]

    if len(leituras_recentes) < 2:
        leituras_recentes = leituras_ordenadas[-10:]

    # Procura se em algum momento recente houve queda rápida que se manteve
    for i in range(len(leituras_recentes)):
        l_antes = leituras_recentes[i]
        janela_limite = l_antes.data_hora + timedelta(hours=janela_horas)
        
        for j in range(i + 1, len(leituras_recentes)):
            l_depois = leituras_recentes[j]
            if l_depois.data_hora > janela_limite:
                break
            
            queda = l_antes.peso_kg - l_depois.peso_kg
            # Queda rápida detectada e a perda de peso se manteve até a leitura atual
            if queda >= limiar_queda_kg and (l_antes.peso_kg - leitura_atual.peso_kg) >= (limiar_queda_kg * 0.8):
                return True

    return False


def extrair_features_sinal(
    leituras: List[LeituraPura],
    peso_tara_kg: Optional[float],
    data_referencia: datetime
) -> FeaturesSinal:
    leituras_validas = limpar_leituras_invalidas(leituras)
    tara_valida = peso_tara_kg is not None

    if not leituras_validas:
        return FeaturesSinal(
            peso_noturno_atual=0.0,
            delta_24h=0.0,
            delta_7d=0.0,
            queda_abrupta_detectada=False,
            reserva_liquida_alimento_kg=0.0,
            dados_suficientes=False,
            tara_definida=tara_valida
        )

    peso_noturno = extrair_peso_noturno(leituras_validas, data_referencia)
    peso_base = peso_noturno if peso_noturno is not None else leituras_validas[-1].peso_kg

    peso_ontem = extrair_peso_noturno(leituras_validas, data_referencia - timedelta(days=1))
    delta_24h = round(peso_base - peso_ontem, 2) if peso_ontem is not None else 0.0

    # Busca no 7º dia; se faltar leitura exata, busca em dias vizinhos (6, 8, 5)
    peso_7d = extrair_peso_noturno(leituras_validas, data_referencia - timedelta(days=7))
    if peso_7d is None:
        for offset in (6, 8, 5):
            peso_7d = extrair_peso_noturno(leituras_validas, data_referencia - timedelta(days=offset))
            if peso_7d is not None:
                break
    delta_7d = round(peso_base - peso_7d, 2) if peso_7d is not None else 0.0

    queda_abrupta = detectar_queda_abrupta(leituras_validas)
    tara_num = peso_tara_kg if tara_valida else 0.0
    reserva_liquida = round(max(0.0, peso_base - tara_num), 2)

    return FeaturesSinal(
        peso_noturno_atual=peso_base,
        delta_24h=delta_24h,
        delta_7d=delta_7d,
        queda_abrupta_detectada=queda_abrupta,
        reserva_liquida_alimento_kg=reserva_liquida,
        dados_suficientes=True,
        tara_definida=tara_valida
    )