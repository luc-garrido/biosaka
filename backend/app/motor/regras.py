"""
==============================================================================
ARQUIVO: app/motor/regras.py
PAPEL: "O Cérebro Biológico / Os 4 Especialistas em Abelhas"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo contém a lógica das 4 regras de negócio biológicas do Biosaka.
Cada função aqui dentro responde a uma pergunta específica sobre o estado da colmeia.

POR QUE ELE EXISTE SEPARADO?
Separar as regras biológicas do restante do sistema permite que você teste cada
cálculo isoladamente (usando o simulador.py) sem precisar ligar o banco de dados
e sem precisar de internet. É ciência apícola codificada em Python.

AS 4 REGRAS QUE FICAM AQUI:

1. RF01 - ABERTURA SEGURA DA CAIXA:
   - Pergunta: "O apicultor pode abrir a caixa hoje para fazer revisão?"
   - Lógica: Olha o clima. Se a temperatura for menor que 18°C, se estiver chovendo
     ou se o vento estiver forte, abrir a caixa esfria os favos e mata as larvas/crias.
   - Resposta: Bloqueia abertura se o clima for perigoso.

2. RF03 - PONTO DE COLHEITA DE MEL:
   - Pergunta: "O mel já está pronto para ser colhido?"
   - Lógica: Quando a melgueira está cheia, o peso para de subir e fica estável por
     alguns dias. Isso indica que as abelhas terminaram de desidratar o néctar e
     já fecharam os favos com cera (mel operculado / maduro).
   - Resposta: Sugere colheita se o peso atingiu o teto da capacidade.

3. RF04 - ALERTA DE FOME E ESGOTAMENTO DE RESERVAS:
   - Pergunta: "As abelhas estão sem comida?"
   - Lógica: Subtrai o peso da madeira da caixa (a tara). Se a reserva restante
     cair abaixo de 3.0 kg (ou estiver em queda diária contínua na entressafra),
     o enxame corre risco iminente de morte por inanição.
   - Resposta: Dispara alerta vermelho de alimentação urgente com xarope.

4. RF05 - ALERTA DE ENXAMEAÇÃO:
   - Pergunta: "As abelhas fugiram ou enxamearam?"
   - Lógica: Se a balança registrar uma perda brusca de peso (ex: queda de 1.5 kg a 3.0 kg
     em apenas 2 horas) E NÃO houver registro de que o apicultor foi lá colher mel,
     significa que a rainha velha foi embora levando metade da colônia com ela!
   - Resposta: Dispara alerta vermelho de enxameação imediata.
==============================================================================
"""
from typing import List, Optional

from app.motor.tipos import (
    Semaforo,
    Confianca,
    CodigoRegra,
    ResultadoRegra,
    FeaturesSinal,
    ContextoClima,
)

def avaliar_abertura_segura(clima: Optional[ContextoClima]) -> ResultadoRegra:
    if clima is None or not clima.dados_confiaveis:
        return ResultadoRegra(
            codigo=CodigoRegra.RF01,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo="Dados Climáticos Insuficientes",
            confianca=Confianca.BAIXA,
            acao_sugerida="Aguarde conexão ou verifique o clima manualmente antes de abrir."
        )

    motivos_desfavoraveis = []
    motivos_cautela = []

    if clima.chovendo:
        motivos_desfavoraveis.append("Chuva ativa")

    if clima.temperatura_celsius < 16:
        motivos_desfavoraveis.append(f"Frio crítico ({clima.temperatura_celsius}°C)")
    elif 16 <= clima.temperatura_celsius <= 19:
        motivos_cautela.append(f"Frio moderado ({clima.temperatura_celsius}°C)")
    elif clima.temperatura_celsius > 35:
        motivos_cautela.append(f"Calor extremo ({clima.temperatura_celsius}°C)")
    
    if clima.umidade_pct > 85.0:
        motivos_cautela.append(f"Umidade muito alta ({clima.umidade_pct}%)")

    if clima.vento_kmh > 25:
        motivos_desfavoraveis.append(f"Vento forte ({clima.vento_kmh}km/h)")
    elif 15 <= clima.vento_kmh <= 25:
        motivos_cautela.append(f"Vento moderado ({clima.vento_kmh}km/h)")

    if motivos_desfavoraveis:
        return ResultadoRegra(
            codigo=CodigoRegra.RF01,
            semaforo=Semaforo.AMARELO,
            disparou=True,
            motivo="; ".join(motivos_desfavoraveis),
            confianca=Confianca.ALTA,
            acao_sugerida="Não abra a colmeia hoje. Condições climáticas perigosas para as crias."
        )

    if motivos_cautela:
        return ResultadoRegra(
            codigo=CodigoRegra.RF01,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo="; ".join(motivos_cautela),
            confianca=Confianca.ALTA,
            acao_sugerida="Abra a colmeia com cuidado e rapidez, ou espere o tempo firmar."
        )

    return ResultadoRegra(
        codigo=CodigoRegra.RF01,
        semaforo=Semaforo.VERDE,
        disparou=False,
        motivo="Clima Ideal",
        confianca=Confianca.ALTA,
        acao_sugerida="Pode abrir a colmeia sem riscos."
    )


def avaliar_ponto_colheita(
    features: FeaturesSinal,
    peso_meta_melgueira_kg: float = 15.0
) -> ResultadoRegra:
    if not features.dados_suficientes:
        return ResultadoRegra(
            codigo=CodigoRegra.RF03,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo="Dados insuficientes da balança para avaliar colheita.",
            confianca=Confianca.BAIXA,
            acao_sugerida="Aguarde novas leituras da balança."
        )

    tara_aceitavel = 1.5
    limiar_minimo_melgueira = peso_meta_melgueira_kg - tara_aceitavel  # ex: 13.5 kg

    # 1. Melgueira atingiu a meta e o peso estabilizou (maturação/operculação)
    if features.reserva_liquida_alimento_kg >= peso_meta_melgueira_kg and abs(features.delta_24h) <= 0.3:
        return ResultadoRegra(
            codigo=CodigoRegra.RF03,
            semaforo=Semaforo.VERDE,
            disparou=True,
            motivo=f"Melgueira cheia ({features.reserva_liquida_alimento_kg} kg) e peso estabilizado (platô de maturação).",
            confianca=Confianca.ALTA,
            acao_sugerida="Pode realizar a colheita do mel."
        )
    # 2. Próximo da meta ou com acúmulo ativo em andamento
    elif features.reserva_liquida_alimento_kg >= limiar_minimo_melgueira:
        return ResultadoRegra(
            codigo=CodigoRegra.RF03,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo=f"Melgueira em enchimento/maturação ativa ({features.reserva_liquida_alimento_kg} kg).",
            confianca=Confianca.ALTA,
            acao_sugerida="Aguarde a estabilização do peso para garantir mel 100% maduro e operculado."
        )
    # 3. Abaixo da capacidade de colheita
    else:
        return ResultadoRegra(
            codigo=CodigoRegra.RF03,
            semaforo=Semaforo.VERDE,
            disparou=False,
            motivo=f"Volume de mel ({features.reserva_liquida_alimento_kg} kg) ainda abaixo da capacidade de colheita ({peso_meta_melgueira_kg} kg).",
            confianca=Confianca.ALTA,
            acao_sugerida="Nenhum manejo de colheita necessário no momento."
        )


def avaliar_risco_fome(features: FeaturesSinal) -> ResultadoRegra:
    if not features.dados_suficientes:
        return ResultadoRegra(
            codigo=CodigoRegra.RF04,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo="Dados insuficientes da balança para avaliar reservas de alimento.",
            confianca=Confianca.BAIXA,
            acao_sugerida="Verifique a conexão da balança e aguarde novas leituras."
        )

    limiar_vermelho = 3.0
    limiar_amarelo = 5.0

    if features.reserva_liquida_alimento_kg < limiar_vermelho:
        return ResultadoRegra(
            codigo=CodigoRegra.RF04,
            semaforo=Semaforo.VERMELHO,
            disparou=True,
            motivo=f"Reserva de alimento crítica ({features.reserva_liquida_alimento_kg} kg, abaixo do mínimo de {limiar_vermelho} kg).",
            confianca=Confianca.ALTA,
            acao_sugerida="ALIMENTE SUAS ABELHAS AGORA! Risco iminente de inanição."
        )
    if features.reserva_liquida_alimento_kg <= limiar_amarelo and (features.delta_7d < 0 or features.delta_24h < 0):
        perda = abs(features.delta_7d) if features.delta_7d < 0 else abs(features.delta_24h)
        return ResultadoRegra(
            codigo=CodigoRegra.RF04,
            semaforo=Semaforo.AMARELO,
            disparou=True,
            motivo=f"Reserva em declínio ({features.reserva_liquida_alimento_kg} kg com perda de {perda} kg).",
            confianca=Confianca.ALTA,
            acao_sugerida="Verifique a reserva e prepare alimentação de reforço."
        )
    return ResultadoRegra(
        codigo=CodigoRegra.RF04,
        semaforo=Semaforo.VERDE,
        disparou=False,
        motivo=f"Reserva estável e suficiente ({features.reserva_liquida_alimento_kg} kg).",
        confianca=Confianca.ALTA,
        acao_sugerida="Não é necessário alimentar no momento."
    )


def avaliar_enxameacao(features: FeaturesSinal, houve_manejo: bool = False) -> ResultadoRegra:
    if not features.dados_suficientes:
        return ResultadoRegra(
            codigo=CodigoRegra.RF05,
            semaforo=Semaforo.AMARELO,
            disparou=False,
            motivo="Sem dados suficientes da balança para monitorar enxameação.",
            confianca=Confianca.BAIXA,
            acao_sugerida="Verifique a transmissão da balança."
        )

    if features.queda_abrupta_detectada:
        if not houve_manejo:
            return ResultadoRegra(
                codigo=CodigoRegra.RF05,
                semaforo=Semaforo.VERMELHO,
                disparou=True,
                motivo="Queda brusca de peso detectada nas últimas horas sem registro de manejo ou colheita.",
                confianca=Confianca.ALTA,
                acao_sugerida="Possível enxameação! Verifique galhos e árvores próximas imediatamente para resgatar o enxame."
            )
        else:
            return ResultadoRegra(
                codigo=CodigoRegra.RF05,
                semaforo=Semaforo.VERDE,
                disparou=False,
                motivo="Queda brusca de peso compatível com colheita/manejo humano registrado.",
                confianca=Confianca.ALTA,
                acao_sugerida="Nenhum risco de enxameação detectado."
            )

    return ResultadoRegra(
        codigo=CodigoRegra.RF05,
        semaforo=Semaforo.VERDE,
        disparou=False,
        motivo="Estabilidade de peso. Sem indicativo de enxameação.",
        confianca=Confianca.ALTA,
        acao_sugerida="Nenhum risco de enxameação detectado."
    )


def avaliar_todas_regras(
    features: FeaturesSinal,
    clima: Optional[ContextoClima],
    houve_manejo: bool = False
) -> List[ResultadoRegra]:
    return [
        avaliar_abertura_segura(clima),
        avaliar_ponto_colheita(features),
        avaliar_risco_fome(features),
        avaliar_enxameacao(features, houve_manejo)
    ]