"""
==============================================================================
ARQUIVO: app/servicos.py
PAPEL: "O Maestro Orquestrador / A Regra de Negócio da Aplicação"
==============================================================================
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .banco import Colmeia, Inspecao, Leitura, SerieDataset
from .motor.tipos import (
    ContextoClima,
    DiagnosticoFinal,
    FeaturesSinal,
    LeituraPura,
)
from .motor.sinal import extrair_features_sinal
from .motor.regras import avaliar_todas_regras
from .motor.semaforo import consolidar_diagnostico


def carregar_leituras_puras_colmeia(
    db: Session,
    colmeia_id: int,
    data_fim: datetime,
    dias_historico: int = 9
) -> Tuple[List[LeituraPura], Optional[float]]:

    colmeia = db.get(Colmeia, colmeia_id)
    if colmeia is None:
        raise ValueError(f"Colmeia {colmeia_id} não encontrada.")

    tara_kg = float(colmeia.peso_tara_kg) if colmeia.peso_tara_kg is not None else None

    # Busca a série temporal de peso vinculada a esta colmeia
    serie = db.scalars(
        select(SerieDataset).where(
            SerieDataset.colmeia_id == colmeia_id,
            SerieDataset.metrica == "weight"
        )
    ).first()

    if serie is None:
        return [], tara_kg

    data_inicio = data_fim - timedelta(days=dias_historico)
    consulta = (
        select(Leitura)
        .where(
            Leitura.serie_id == serie.id,
            Leitura.instante_original >= data_inicio,
            Leitura.instante_original <= data_fim,
            Leitura.valor_original.isnot(None),
        )
        .order_by(Leitura.instante_original)
    )
    leituras_db = db.scalars(consulta).all()

    leituras_puras = [
        LeituraPura(
            data_hora=l.instante_original,
            peso_kg=float(l.valor_original)
        )
        for l in leituras_db
        if l.valor_original is not None
    ]

    return leituras_puras, tara_kg


def verificar_manejo_recente(
    db: Session,
    colmeia_id: int,
    data_referencia: datetime,
    janela_dias: int = 1
) -> bool:
    """
    Verifica se houve alguma inspeção humana recente registrada no banco para essa colmeia.
    """
    data_limite = (data_referencia - timedelta(days=janela_dias)).date()
    ref_date = data_referencia.date()

    inspecao = db.scalars(
        select(Inspecao).where(
            Inspecao.colmeia_id == colmeia_id,
            Inspecao.data_inspecao >= data_limite,
            Inspecao.data_inspecao <= ref_date,
        )
    ).first()

    return inspecao is not None


def obter_features_colmeia(
    db: Session,
    colmeia_id: int,
    data_referencia: Optional[datetime] = None
) -> FeaturesSinal:
    """
    Extrai as features de sinal (peso noturno, deltas, enxameação) de uma colmeia.
    Se data_referencia for omitida, usa a data da última leitura de peso da série.
    """
    if data_referencia is None:
        serie = db.scalars(
            select(SerieDataset).where(
                SerieDataset.colmeia_id == colmeia_id,
                SerieDataset.metrica == "weight"
            )
        ).first()

        if serie is not None:
            data_referencia = db.scalar(
                select(func.max(Leitura.instante_original)).where(
                    Leitura.serie_id == serie.id
                )
            )

        if data_referencia is None:
            data_referencia = datetime.now()

    leituras_puras, tara_kg = carregar_leituras_puras_colmeia(
        db, colmeia_id, data_fim=data_referencia
    )

    return extrair_features_sinal(
        leituras=leituras_puras,
        peso_tara_kg=tara_kg,
        data_referencia=data_referencia
    )


def diagnosticar_colmeia(
    db: Session,
    colmeia_id: int,
    data_referencia: Optional[datetime] = None,
    clima: Optional[ContextoClima] = None
) -> DiagnosticoFinal:
    """
    Orquestra a coleta de dados da colmeia no banco e executa o motor biológico.
    """
    colmeia = db.get(Colmeia, colmeia_id)
    if colmeia is None:
        raise ValueError(f"Colmeia {colmeia_id} não encontrada.")

    if data_referencia is None:
        serie = db.scalars(
            select(SerieDataset).where(
                SerieDataset.colmeia_id == colmeia_id,
                SerieDataset.metrica == "weight"
            )
        ).first()

        if serie is not None:
            data_referencia = db.scalar(
                select(func.max(Leitura.instante_original)).where(
                    Leitura.serie_id == serie.id
                )
            )

        if data_referencia is None:
            data_referencia = datetime.now()

    leituras_puras, tara_kg = carregar_leituras_puras_colmeia(
        db, colmeia_id, data_fim=data_referencia
    )
    houve_manejo = verificar_manejo_recente(db, colmeia_id, data_referencia)

    features = extrair_features_sinal(
        leituras=leituras_puras,
        peso_tara_kg=tara_kg,
        data_referencia=data_referencia
    )

    regras = avaliar_todas_regras(
        features=features,
        clima=clima,
        houve_manejo=houve_manejo
    )

    return consolidar_diagnostico(regras)
