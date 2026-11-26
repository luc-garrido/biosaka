"""Testes do motor biologico sem banco: sinal, regras e clima."""
from datetime import datetime, timedelta

from backend.app import clima
from backend.app.motor.regras import avaliar_enxameacao, avaliar_ponto_colheita
from backend.app.motor.sinal import extrair_features_sinal
from backend.app.motor.tipos import LeituraPura, Semaforo

REF = datetime(2017, 6, 30, 3, 0)


def noites(pesos_por_dia):
    """Uma leitura por noite (02h), do dia mais antigo ate REF."""
    total = len(pesos_por_dia)
    return [LeituraPura(REF.replace(hour=2) - timedelta(days=total - 1 - i), p)
            for i, p in enumerate(pesos_por_dia)]


def test_uma_leitura_nao_e_historico_suficiente():
    features = extrair_features_sinal([LeituraPura(REF.replace(hour=2), 30.0)], 10.0, REF)
    assert features.dados_suficientes is False
    assert features.delta_24h is None
    regra = avaliar_ponto_colheita(features)
    assert regra.disparou is False
    assert "insuficientes" in regra.motivo.lower()


def test_historico_de_oito_noites_e_suficiente():
    features = extrair_features_sinal(noites([40.0] * 8), 10.0, REF)
    assert features.dados_suficientes is True
    assert features.delta_24h == 0.0 and features.delta_7d == 0.0


def test_queda_brusca_so_e_explicada_por_manejo_explicito():
    # 7 noites estaveis em 40 kg; ontem a tarde caiu 4 kg em 2 horas e ficou em 36 kg
    leituras = noites([40.0] * 7 + [36.0])
    dia = REF - timedelta(hours=15)
    leituras += [LeituraPura(dia, 40.0), LeituraPura(dia + timedelta(hours=2), 36.0)]
    leituras.sort(key=lambda l: l.data_hora)
    features = extrair_features_sinal(leituras, 10.0, REF)
    assert features.queda_abrupta_detectada is True
    assert avaliar_enxameacao(features, houve_manejo=False).semaforo == Semaforo.VERMELHO
    assert avaliar_enxameacao(features, houve_manejo=True).semaforo == Semaforo.VERDE


def test_clima_com_resposta_vazia_nao_e_confiavel(monkeypatch):
    class Resposta:
        status_code = 200

        def json(self):
            return {}

    clima._CACHE_CLIMA.clear()
    monkeypatch.setattr(clima.httpx, "get", lambda *a, **k: Resposta())
    contexto = clima.consultar_clima(-22.9, -47.06)
    assert contexto.dados_confiaveis is False
