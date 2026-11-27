"""Testes do orquestrador (servicos.py): banco real -> motor -> semaforo.

Usam o mesmo schema MySQL temporario da fixture `client`. Os horarios sao fixos
(junho de 2017, no formato do dataset Beehive Metrics) e a tara da colmeia de
teste e 4,125 kg (ver fixture `colmeia`).
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from backend.app import servicos
from backend.app.motor.tipos import (CodigoRegra, Confianca, ContextoClima, Semaforo)

REF = datetime(2017, 6, 10, 12, 0)
CLIMA_IDEAL = ContextoClima(25.0, False, 5.0, True, 50.0)


def semear(colmeia_id, leituras, metrica="weight", codigo=None):
    """Grava uma serie e suas leituras [(datetime, valor|None)] direto no banco."""
    from backend.app.banco import Leitura, SerieDataset, SessionLocal
    with SessionLocal() as db:
        serie = SerieDataset(colmeia_id=colmeia_id, codigo=codigo or f"svc-{colmeia_id}-{metrica}",
                             metrica=metrica, fonte_url="https://example.invalid",
                             arquivo_origem="teste.csv", sha256_arquivo="b" * 64, unidade_original="kg")
        db.add(serie)
        db.flush()
        for linha, (instante, valor) in enumerate(leituras, 2):
            db.add(Leitura(serie_id=serie.id, instante_original=instante, valor_original=valor,
                           texto_valor_original="" if valor is None else str(valor), linha_origem=linha))
        db.commit()
        return serie.id


def noites(peso, dias=10, referencia=REF, extras=()):
    """Duas leituras de madrugada por dia (02h e 03h), com o mesmo peso, mais `extras`."""
    leituras = []
    for i in range(dias):
        madrugada = (referencia - timedelta(days=i)).replace(hour=2, minute=0)
        leituras += [(madrugada, Decimal(str(peso))), (madrugada + timedelta(hours=1), Decimal(str(peso)))]
    return sorted(leituras + list(extras))


def sessao():
    from backend.app.banco import SessionLocal
    return SessionLocal()


def regra(diagnostico, codigo):
    return next(r for r in diagnostico.detalhes_regras if r.codigo == codigo)


# --------------------------------------------------------------------------
# carregar_leituras_puras_colmeia
# --------------------------------------------------------------------------

def test_carrega_so_a_janela_de_9_dias_e_ignora_valores_nulos(colmeia):
    semear(colmeia["id"], [
        (REF - timedelta(days=9, seconds=1), Decimal("1.0")),   # antes da janela
        (REF - timedelta(days=9), Decimal("2.0")),              # limite inferior incluido
        (REF - timedelta(hours=1), None),                       # ausente: nunca vira zero
        (REF, Decimal("3.0")),                                  # limite superior incluido
        (REF + timedelta(seconds=1), Decimal("4.0")),           # depois da referencia
    ])
    with sessao() as db:
        leituras, tara = servicos.carregar_leituras_puras_colmeia(db, colmeia["id"], REF)
    assert [l.peso_kg for l in leituras] == [2.0, 3.0]
    assert tara == pytest.approx(4.125)


def test_colmeia_sem_serie_devolve_lista_vazia_e_a_tara(colmeia):
    with sessao() as db:
        assert servicos.carregar_leituras_puras_colmeia(db, colmeia["id"], REF) == ([], pytest.approx(4.125))


def test_serie_de_outra_metrica_nao_entra_como_peso(colmeia):
    semear(colmeia["id"], [(REF, Decimal("22.5"))], metrica="temperature")
    with sessao() as db:
        leituras, _ = servicos.carregar_leituras_puras_colmeia(db, colmeia["id"], REF)
    assert leituras == []


def test_colmeia_sem_tara_devolve_tara_none(client, colmeia):
    resposta = client.post("/colmeias", json={"apiario_id": colmeia["apiario_id"], "codigo": "SEM-TARA"})
    assert resposta.status_code == 201
    with sessao() as db:
        _, tara = servicos.carregar_leituras_puras_colmeia(db, resposta.json()["id"], REF)
    assert tara is None


def test_colmeia_inexistente_levanta_erro_claro(client):
    with sessao() as db:
        with pytest.raises(ValueError, match="não encontrada"):
            servicos.carregar_leituras_puras_colmeia(db, 999999999, REF)
        with pytest.raises(ValueError, match="não encontrada"):
            servicos.diagnosticar_colmeia(db, 999999999, REF, CLIMA_IDEAL)


# --------------------------------------------------------------------------
# verificar_manejo_recente
# --------------------------------------------------------------------------

def inspecionar(client, colmeia_id, dia, manejo):
    resposta = client.post("/inspecoes", json={"colmeia_id": colmeia_id, "data_inspecao": dia,
                                               "houve_manejo": manejo})
    assert resposta.status_code == 201, resposta.text


def test_manejo_recente_considera_hoje_e_ontem_mas_nao_dois_dias_atras(client, colmeia):
    inspecionar(client, colmeia["id"], "2017-06-08", True)
    with sessao() as db:
        assert servicos.verificar_manejo_recente(db, colmeia["id"], REF) is False
    inspecionar(client, colmeia["id"], "2017-06-09", True)
    with sessao() as db:
        assert servicos.verificar_manejo_recente(db, colmeia["id"], REF) is True


def test_inspecao_sem_manejo_nao_conta(client, colmeia):
    inspecionar(client, colmeia["id"], "2017-06-10", False)
    with sessao() as db:
        assert servicos.verificar_manejo_recente(db, colmeia["id"], REF) is False


def test_manejo_de_outra_colmeia_nao_conta(client, colmeia):
    outra = client.post("/colmeias", json={"apiario_id": colmeia["apiario_id"], "codigo": "OUTRA"}).json()
    inspecionar(client, outra["id"], "2017-06-10", True)
    with sessao() as db:
        assert servicos.verificar_manejo_recente(db, colmeia["id"], REF) is False


# --------------------------------------------------------------------------
# obter_features_colmeia / diagnosticar_colmeia
# --------------------------------------------------------------------------

def test_sem_data_de_referencia_usa_a_ultima_leitura_da_serie(colmeia):
    semear(colmeia["id"], noites(30.0))
    with sessao() as db:
        f = servicos.obter_features_colmeia(db, colmeia["id"])
    assert f.possui_leituras and f.dados_suficientes
    assert f.peso_noturno_atual == 30.0
    assert f.reserva_liquida_alimento_kg == pytest.approx(25.875, abs=0.005)  # o motor arredonda a 2 casas


def test_melgueira_cheia_e_estavel_gera_verde_de_colheita(colmeia):
    semear(colmeia["id"], noites(30.0))
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL)
    assert d.semaforo == Semaforo.VERDE and regra(d, CodigoRegra.RF03).disparou is True
    assert "colheita" in d.frase_modo_avo.lower()


def test_reserva_abaixo_de_3_kg_gera_vermelho_de_fome(colmeia):
    semear(colmeia["id"], noites(5.0))  # 5,0 - 4,125 de tara = 0,875 kg
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL)
    assert d.semaforo == Semaforo.VERMELHO and regra(d, CodigoRegra.RF04).disparou is True
    assert "sem comida" in d.frase_modo_avo


QUEDA = [(REF - timedelta(hours=3), Decimal("30.0")), (REF - timedelta(hours=2), Decimal("30.0")),
         (REF - timedelta(hours=1), Decimal("27.0")), (REF, Decimal("26.9"))]


def test_queda_brusca_sem_inspecao_gera_vermelho_de_enxameacao(colmeia):
    semear(colmeia["id"], noites(30.0, extras=QUEDA))
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL)
    assert d.semaforo == Semaforo.VERMELHO and regra(d, CodigoRegra.RF05).disparou is True
    assert "enxameação" in d.frase_modo_avo


def test_queda_brusca_com_manejo_registrado_nao_vira_alerta(client, colmeia):
    semear(colmeia["id"], noites(30.0, extras=QUEDA))
    inspecionar(client, colmeia["id"], "2017-06-10", True)
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL)
    assert regra(d, CodigoRegra.RF05).semaforo == Semaforo.VERDE
    assert d.semaforo != Semaforo.VERMELHO


def test_pesos_negativos_do_dataset_sao_descartados_antes_do_calculo(colmeia):
    # o CSV real tem pesos negativos (ruido do sensor); nao podem derrubar a media noturna
    ruido = [((REF - timedelta(days=i)).replace(hour=2, minute=30), Decimal("-0.115216")) for i in range(10)]
    semear(colmeia["id"], noites(30.0, extras=ruido))
    with sessao() as db:
        f = servicos.obter_features_colmeia(db, colmeia["id"], REF)
    assert f.peso_noturno_atual == 30.0
    with sessao() as db:
        assert servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL).semaforo != Semaforo.VERMELHO


def test_colmeia_sem_leituras_fica_amarela_com_confianca_baixa(colmeia):
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, CLIMA_IDEAL)
    assert d.semaforo == Semaforo.AMARELO and d.confianca == Confianca.BAIXA
    assert regra(d, CodigoRegra.RF04).disparou is False   # sem dado nao pode virar alerta de fome


def test_sem_clima_o_diagnostico_cai_em_amarelo_mesmo_com_balanca_ok(colmeia):
    semear(colmeia["id"], noites(30.0))
    with sessao() as db:
        d = servicos.diagnosticar_colmeia(db, colmeia["id"], REF, None)
    assert d.semaforo == Semaforo.AMARELO
    assert regra(d, CodigoRegra.RF01).confianca == Confianca.BAIXA
