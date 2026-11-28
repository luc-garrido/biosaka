"""Testes unitarios do motor biologico (sinal, regras e semaforo).

Python puro: nao usam banco, rede nem relogio do computador. Todos os horarios
sao fixos para o resultado ser sempre o mesmo.
"""
from datetime import datetime, timedelta

import pytest

from backend.app import clima as modulo_clima
from backend.app.motor.regras import (avaliar_abertura_segura, avaliar_enxameacao,
                                      avaliar_ponto_colheita, avaliar_risco_fome,
                                      avaliar_todas_regras)
from backend.app.motor.semaforo import consolidar_diagnostico
from backend.app.motor.sinal import (detectar_queda_abrupta, extrair_features_sinal,
                                     extrair_peso_noturno, limpar_leituras_invalidas)
from backend.app.motor.tipos import (CodigoRegra, Confianca, ContextoClima, FeaturesSinal,
                                     LeituraPura, ResultadoRegra, Semaforo)

BASE = datetime(2017, 6, 10, 12, 0)
CLIMA_IDEAL = ContextoClima(temperatura_celsius=25.0, chovendo=False, vento_kmh=5.0,
                            dados_confiaveis=True, umidade_pct=50.0)


def clima(**mudancas):
    dados = dict(temperatura_celsius=25.0, chovendo=False, vento_kmh=5.0,
                 dados_confiaveis=True, umidade_pct=50.0)
    dados.update(mudancas)
    return ContextoClima(**dados)


def features(**mudancas):
    dados = dict(peso_noturno_atual=30.0, delta_24h=0.0, delta_7d=0.0,
                 queda_abrupta_detectada=False, reserva_liquida_alimento_kg=10.0,
                 dados_suficientes=True, tara_definida=True, possui_leituras=True)
    dados.update(mudancas)
    return FeaturesSinal(**dados)


def historico_noturno(dias, peso_por_dia, referencia=BASE):
    """Uma leitura as 02h de cada noite, terminando na noite da referencia."""
    leituras = []
    for i in range(dias):
        madrugada = (referencia - timedelta(days=i)).replace(hour=2, minute=0)
        leituras.append(LeituraPura(madrugada, peso_por_dia(i)))
    return leituras


# --------------------------------------------------------------------------
# sinal.py
# --------------------------------------------------------------------------

def test_limpeza_descarta_negativos_e_acima_de_150_kg_e_ordena():
    leituras = [LeituraPura(BASE + timedelta(hours=2), 20.0), LeituraPura(BASE, -0.115216),
                LeituraPura(BASE + timedelta(hours=1), 150.01), LeituraPura(BASE, 150.0),
                LeituraPura(BASE - timedelta(hours=1), 0.0)]
    limpas = limpar_leituras_invalidas(leituras)
    assert [l.peso_kg for l in limpas] == [0.0, 150.0, 20.0]
    assert limpas == sorted(limpas, key=lambda l: l.data_hora)


def test_peso_noturno_usa_janela_22h_as_04h_e_faz_media():
    leituras = [LeituraPura(datetime(2017, 6, 9, 21, 59), 99.0),   # antes da janela
                LeituraPura(datetime(2017, 6, 9, 22, 0), 30.0),
                LeituraPura(datetime(2017, 6, 10, 3, 0), 31.0),
                LeituraPura(datetime(2017, 6, 10, 4, 0), 32.0),    # limite incluido
                LeituraPura(datetime(2017, 6, 10, 4, 1), 99.0)]    # depois da janela
    assert extrair_peso_noturno(leituras, datetime(2017, 6, 10, 12, 0)) == 31.0


def test_peso_noturno_depois_das_22h_olha_a_noite_que_comecou_hoje():
    leituras = [LeituraPura(datetime(2017, 6, 10, 23, 0), 40.0),
                LeituraPura(datetime(2017, 6, 11, 1, 0), 42.0)]
    assert extrair_peso_noturno(leituras, datetime(2017, 6, 10, 22, 30)) == 41.0


def test_peso_noturno_sem_leituras_na_janela_devolve_none():
    assert extrair_peso_noturno([], BASE) is None
    assert extrair_peso_noturno([LeituraPura(BASE, 30.0)], BASE) is None


def test_queda_abrupta_mantida_e_detectada():
    ls = [LeituraPura(BASE + timedelta(hours=h), p)
          for h, p in [(0, 30.0), (1, 30.0), (2, 27.5), (3, 27.4), (4, 27.4)]]
    assert detectar_queda_abrupta(ls) is True


def test_queda_recuperada_nao_e_enxameacao():
    ls = [LeituraPura(BASE + timedelta(hours=h), p)
          for h, p in [(0, 30.0), (1, 27.5), (2, 29.9), (3, 30.0)]]
    assert detectar_queda_abrupta(ls) is False


def test_queda_lenta_demais_para_a_janela_nao_dispara():
    # 2 kg em 12 h: acima do limiar, mas fora da janela de 4 h
    ls = [LeituraPura(BASE + timedelta(hours=h), 30.0 - h / 6) for h in range(0, 13, 2)]
    assert detectar_queda_abrupta(ls) is False


@pytest.mark.parametrize("quantidade", [0, 1])
def test_queda_com_menos_de_duas_leituras_nao_dispara(quantidade):
    assert detectar_queda_abrupta([LeituraPura(BASE, 30.0)][:quantidade]) is False


def test_features_sem_leituras_validas_marcam_possui_leituras_falso():
    f = extrair_features_sinal([LeituraPura(BASE, -5.0)], peso_tara_kg=4.0, data_referencia=BASE)
    assert f.possui_leituras is False and f.dados_suficientes is False
    assert f.reserva_liquida_alimento_kg == 0.0 and f.tara_definida is True


def test_features_com_historico_completo_calculam_deltas_e_reserva():
    # peso cai 0,1 kg por dia: hoje 30,0; ontem 30,1; ha 7 dias 30,7
    leituras = historico_noturno(9, lambda i: 30.0 + 0.1 * i)
    f = extrair_features_sinal(leituras, peso_tara_kg=4.0, data_referencia=BASE)
    assert f.dados_suficientes is True and f.possui_leituras is True
    assert f.peso_noturno_atual == 30.0
    assert f.delta_24h == pytest.approx(-0.1) and f.delta_7d == pytest.approx(-0.7)
    assert f.reserva_liquida_alimento_kg == pytest.approx(26.0)


def test_features_com_poucos_dias_ficam_sem_dados_suficientes():
    f = extrair_features_sinal(historico_noturno(3, lambda i: 30.0), 4.0, BASE)
    assert f.dados_suficientes is False and f.delta_7d is None


def test_features_sem_tara_nao_inventam_reserva_e_sinalizam():
    f = extrair_features_sinal(historico_noturno(9, lambda i: 30.0), None, BASE)
    assert f.tara_definida is False


def test_reserva_liquida_nunca_fica_negativa():
    f = extrair_features_sinal(historico_noturno(9, lambda i: 3.0), 10.0, BASE)
    assert f.reserva_liquida_alimento_kg == 0.0


# --------------------------------------------------------------------------
# regras.py - RF01 abertura segura
# --------------------------------------------------------------------------

@pytest.mark.parametrize("c", [None, clima(dados_confiaveis=False)])
def test_rf01_sem_clima_confiavel_e_amarelo_de_baixa_confianca(c):
    r = avaliar_abertura_segura(c)
    assert (r.semaforo, r.disparou, r.confianca) == (Semaforo.AMARELO, False, Confianca.BAIXA)


def test_rf01_clima_ideal_e_verde():
    r = avaliar_abertura_segura(CLIMA_IDEAL)
    assert (r.semaforo, r.disparou) == (Semaforo.VERDE, False)


@pytest.mark.parametrize("c, trecho", [
    (clima(chovendo=True), "Chuva"),
    (clima(temperatura_celsius=15.9), "Frio crítico"),
    (clima(vento_kmh=25.1), "Vento forte"),
])
def test_rf01_condicoes_perigosas_bloqueiam_a_abertura(c, trecho):
    r = avaliar_abertura_segura(c)
    assert r.disparou is True and r.semaforo == Semaforo.AMARELO and trecho in r.motivo


@pytest.mark.parametrize("c, trecho", [
    (clima(temperatura_celsius=16.0), "Frio moderado"),
    (clima(temperatura_celsius=19.0), "Frio moderado"),
    (clima(temperatura_celsius=35.1), "Calor extremo"),
    (clima(umidade_pct=85.1), "Umidade"),
    (clima(vento_kmh=15.0), "Vento moderado"),
    (clima(vento_kmh=25.0), "Vento moderado"),
])
def test_rf01_condicoes_limitrofes_pedem_cautela_sem_bloquear(c, trecho):
    r = avaliar_abertura_segura(c)
    assert r.disparou is False and r.semaforo == Semaforo.AMARELO and trecho in r.motivo


@pytest.mark.parametrize("c", [clima(temperatura_celsius=19.01), clima(temperatura_celsius=35.0),
                               clima(vento_kmh=14.9), clima(umidade_pct=85.0)])
def test_rf01_bordas_do_lado_seguro_ficam_verdes(c):
    assert avaliar_abertura_segura(c).semaforo == Semaforo.VERDE


def test_rf01_varios_motivos_aparecem_juntos():
    r = avaliar_abertura_segura(clima(chovendo=True, vento_kmh=30.0))
    assert "Chuva" in r.motivo and "Vento forte" in r.motivo


# --------------------------------------------------------------------------
# regras.py - RF03 colheita
# --------------------------------------------------------------------------

def test_rf03_melgueira_cheia_e_estavel_libera_colheita():
    r = avaliar_ponto_colheita(features(reserva_liquida_alimento_kg=15.0, delta_24h=0.3))
    assert (r.semaforo, r.disparou) == (Semaforo.VERDE, True)


def test_rf03_cheia_mas_ainda_ganhando_peso_aguarda():
    r = avaliar_ponto_colheita(features(reserva_liquida_alimento_kg=16.0, delta_24h=0.31))
    assert (r.semaforo, r.disparou) == (Semaforo.AMARELO, False)


def test_rf03_proxima_da_meta_fica_em_enchimento():
    r = avaliar_ponto_colheita(features(reserva_liquida_alimento_kg=13.5))
    assert (r.semaforo, r.disparou) == (Semaforo.AMARELO, False)


def test_rf03_abaixo_da_capacidade_nao_pede_manejo():
    r = avaliar_ponto_colheita(features(reserva_liquida_alimento_kg=13.49))
    assert (r.semaforo, r.disparou) == (Semaforo.VERDE, False)


def test_rf03_meta_da_melgueira_e_configuravel():
    f = features(reserva_liquida_alimento_kg=8.0, delta_24h=0.0)
    assert avaliar_ponto_colheita(f, peso_meta_melgueira_kg=8.0).disparou is True
    assert avaliar_ponto_colheita(f).disparou is False


@pytest.mark.parametrize("f", [features(dados_suficientes=False), features(tara_definida=False)])
def test_rf03_sem_dados_ou_sem_tara_e_amarelo_de_baixa_confianca(f):
    r = avaliar_ponto_colheita(f)
    assert (r.semaforo, r.disparou, r.confianca) == (Semaforo.AMARELO, False, Confianca.BAIXA)


# --------------------------------------------------------------------------
# regras.py - RF04 fome
# --------------------------------------------------------------------------

def test_rf04_reserva_abaixo_de_3_kg_e_vermelha():
    r = avaliar_risco_fome(features(reserva_liquida_alimento_kg=2.99))
    assert (r.semaforo, r.disparou, r.confianca) == (Semaforo.VERMELHO, True, Confianca.ALTA)


def test_rf04_exatamente_3_kg_ja_nao_e_vermelha():
    assert avaliar_risco_fome(features(reserva_liquida_alimento_kg=3.0)).semaforo != Semaforo.VERMELHO


def test_rf04_reserva_baixa_e_em_queda_e_amarela_e_dispara():
    r = avaliar_risco_fome(features(reserva_liquida_alimento_kg=4.5, delta_24h=-0.2, delta_7d=0.0))
    assert (r.semaforo, r.disparou) == (Semaforo.AMARELO, True)


def test_rf04_reserva_baixa_mas_estavel_fica_verde():
    r = avaliar_risco_fome(features(reserva_liquida_alimento_kg=4.5, delta_24h=0.0, delta_7d=0.1))
    assert r.semaforo == Semaforo.VERDE


def test_rf04_reserva_alta_fica_verde_mesmo_com_queda():
    r = avaliar_risco_fome(features(reserva_liquida_alimento_kg=10.0, delta_24h=-1.0))
    assert r.semaforo == Semaforo.VERDE


def test_rf04_sem_nenhuma_leitura_nao_vira_alerta_de_fome():
    r = avaliar_risco_fome(features(possui_leituras=False, dados_suficientes=False,
                                    reserva_liquida_alimento_kg=0.0))
    assert (r.semaforo, r.disparou, r.confianca) == (Semaforo.AMARELO, False, Confianca.BAIXA)


def test_rf04_sem_tara_nao_calcula_reserva():
    r = avaliar_risco_fome(features(tara_definida=False, reserva_liquida_alimento_kg=0.0))
    assert (r.semaforo, r.disparou) == (Semaforo.AMARELO, False)


def test_rf04_reserva_critica_alerta_mesmo_sem_historico_suficiente():
    r = avaliar_risco_fome(features(dados_suficientes=False, reserva_liquida_alimento_kg=1.0))
    assert r.semaforo == Semaforo.VERMELHO


def test_rf04_reserva_ok_sem_historico_suficiente_fica_amarela():
    r = avaliar_risco_fome(features(dados_suficientes=False, reserva_liquida_alimento_kg=10.0))
    assert (r.semaforo, r.confianca) == (Semaforo.AMARELO, Confianca.BAIXA)


# --------------------------------------------------------------------------
# regras.py - RF05 enxameacao
# --------------------------------------------------------------------------

def test_rf05_queda_brusca_sem_manejo_e_vermelha():
    r = avaliar_enxameacao(features(queda_abrupta_detectada=True))
    assert (r.semaforo, r.disparou) == (Semaforo.VERMELHO, True)


def test_rf05_queda_brusca_com_manejo_registrado_nao_alerta():
    r = avaliar_enxameacao(features(queda_abrupta_detectada=True), houve_manejo=True)
    assert (r.semaforo, r.disparou) == (Semaforo.VERDE, False)


def test_rf05_peso_estavel_fica_verde():
    assert avaliar_enxameacao(features()).semaforo == Semaforo.VERDE


def test_rf05_sem_dados_suficientes_fica_amarela():
    r = avaliar_enxameacao(features(dados_suficientes=False, queda_abrupta_detectada=True))
    assert (r.semaforo, r.disparou, r.confianca) == (Semaforo.AMARELO, False, Confianca.BAIXA)


def test_todas_as_regras_devolvem_as_quatro_na_ordem():
    regras = avaliar_todas_regras(features(), CLIMA_IDEAL)
    assert [r.codigo for r in regras] == [CodigoRegra.RF01, CodigoRegra.RF03,
                                          CodigoRegra.RF04, CodigoRegra.RF05]


# --------------------------------------------------------------------------
# semaforo.py
# --------------------------------------------------------------------------

def regra(codigo, cor, disparou=False, motivo="x", confianca=Confianca.ALTA):
    return ResultadoRegra(codigo=codigo, semaforo=cor, disparou=disparou,
                          motivo=motivo, confianca=confianca)


def test_vermelho_tem_prioridade_sobre_colheita_e_clima():
    d = consolidar_diagnostico(avaliar_todas_regras(
        features(queda_abrupta_detectada=True, reserva_liquida_alimento_kg=20.0),
        clima(chovendo=True)))
    assert d.semaforo == Semaforo.VERMELHO and "enxameação" in d.frase_modo_avo


def test_enxameacao_vence_fome_na_escolha_da_frase():
    d = consolidar_diagnostico(avaliar_todas_regras(
        features(queda_abrupta_detectada=True, reserva_liquida_alimento_kg=1.0), CLIMA_IDEAL))
    assert d.semaforo == Semaforo.VERMELHO and "enxameação" in d.frase_modo_avo


def test_fome_sozinha_gera_frase_de_alimentar():
    d = consolidar_diagnostico(avaliar_todas_regras(
        features(reserva_liquida_alimento_kg=1.0), CLIMA_IDEAL))
    assert d.semaforo == Semaforo.VERMELHO and "xarope" in d.frase_modo_avo


def test_tudo_verde_com_melgueira_cheia_anuncia_colheita():
    d = consolidar_diagnostico(avaliar_todas_regras(
        features(reserva_liquida_alimento_kg=20.0, delta_24h=0.0), CLIMA_IDEAL))
    assert d.semaforo == Semaforo.VERDE and "colheita" in d.frase_modo_avo.lower()


def test_tudo_verde_sem_colheita_diz_que_esta_tranquilo():
    d = consolidar_diagnostico(avaliar_todas_regras(features(reserva_liquida_alimento_kg=8.0), CLIMA_IDEAL))
    assert d.semaforo == Semaforo.VERDE and "tranquilo" in d.frase_modo_avo.lower()


def test_clima_ausente_rebaixa_para_amarelo_com_aviso_de_clima():
    d = consolidar_diagnostico(avaliar_todas_regras(features(reserva_liquida_alimento_kg=8.0), None))
    assert d.semaforo == Semaforo.AMARELO and "meteorológicos" in d.frase_modo_avo
    assert d.confianca == Confianca.BAIXA


def test_clima_desfavoravel_manda_nao_abrir():
    d = consolidar_diagnostico(avaliar_todas_regras(features(reserva_liquida_alimento_kg=8.0),
                                                    clima(chovendo=True)))
    assert d.semaforo == Semaforo.AMARELO and "Não abra" in d.frase_modo_avo


def test_reserva_em_declinio_tem_prioridade_entre_os_amarelos():
    d = consolidar_diagnostico(avaliar_todas_regras(
        features(reserva_liquida_alimento_kg=4.5, delta_24h=-0.3), clima(chovendo=True)))
    assert d.semaforo == Semaforo.AMARELO and "declínio" in d.frase_modo_avo


def test_confianca_geral_e_a_pior_entre_as_regras():
    base = [regra(CodigoRegra.RF01, Semaforo.VERDE), regra(CodigoRegra.RF04, Semaforo.VERDE)]
    assert consolidar_diagnostico(base).confianca == Confianca.ALTA
    media = base + [regra(CodigoRegra.RF05, Semaforo.VERDE, confianca=Confianca.MEDIA)]
    assert consolidar_diagnostico(media).confianca == Confianca.MEDIA
    baixa = media + [regra(CodigoRegra.RF03, Semaforo.AMARELO, confianca=Confianca.BAIXA)]
    assert consolidar_diagnostico(baixa).confianca == Confianca.BAIXA


def test_diagnostico_preserva_o_detalhe_de_cada_regra():
    regras = avaliar_todas_regras(features(), CLIMA_IDEAL)
    assert consolidar_diagnostico(regras).detalhes_regras == regras

# --------------------------------------------------------------------------
# historico, manejo e clima
# --------------------------------------------------------------------------

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

    modulo_clima._CACHE_CLIMA.clear()
    monkeypatch.setattr(modulo_clima.httpx, "get", lambda *a, **k: Resposta())
    contexto = modulo_clima.consultar_clima(-22.9, -47.06)
    assert contexto.dados_confiaveis is False
