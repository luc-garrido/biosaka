"""Testes do cliente de clima (Open-Meteo) sem acessar a internet.

httpx.get e substituido por uma funcao falsa; o cache em memoria e limpo a cada teste.
"""
import pytest

from backend.app import clima as modulo_clima

RESPOSTA_BOA = {"current": {"temperature_2m": 22.5, "relative_humidity_2m": 60,
                            "precipitation": 0.0, "wind_speed_10m": 8.0}}


class RespostaFalsa:
    def __init__(self, corpo=None, status_code=200):
        self.status_code = status_code
        self._corpo = corpo if corpo is not None else {}

    def json(self):
        return self._corpo


@pytest.fixture(autouse=True)
def limpar_cache():
    modulo_clima._CACHE_CLIMA.clear()
    yield
    modulo_clima._CACHE_CLIMA.clear()


@pytest.fixture
def rede(monkeypatch):
    """Registra as chamadas e permite escolher o que a 'internet' devolve."""
    estado = {"chamadas": [], "resposta": RespostaFalsa(RESPOSTA_BOA), "erro": None}

    def falso(url, params=None, timeout=None):
        estado["chamadas"].append({"url": url, "params": params, "timeout": timeout})
        if estado["erro"]:
            raise estado["erro"]
        return estado["resposta"]

    monkeypatch.setattr(modulo_clima.httpx, "get", falso)
    return estado


def corpo(**campos):
    atual = dict(RESPOSTA_BOA["current"])
    atual.update(campos)
    return {"current": atual}


def test_consulta_valida_vira_contexto_confiavel(rede):
    c = modulo_clima.consultar_clima(-22.9, -47.06)
    assert c.dados_confiaveis is True
    assert (c.temperatura_celsius, c.umidade_pct, c.vento_kmh, c.chovendo) == (22.5, 60.0, 8.0, False)


def test_consulta_usa_timeout_curto_e_pede_os_campos_necessarios(rede):
    modulo_clima.consultar_clima(-22.9, -47.06)
    chamada = rede["chamadas"][0]
    assert chamada["timeout"] is not None and chamada["timeout"] <= 5.0
    for campo in modulo_clima.CAMPOS_CLIMA:
        assert campo in chamada["params"]["current"]


@pytest.mark.parametrize("chuva, esperado", [(0.0, False), (0.1, False), (0.11, True), (3.0, True)])
def test_chuva_so_conta_acima_de_0_1_mm(rede, chuva, esperado):
    rede["resposta"] = RespostaFalsa(corpo(precipitation=chuva))
    assert modulo_clima.consultar_clima(-22.9, -47.06).chovendo is esperado


def test_segunda_consulta_usa_o_cache(rede):
    modulo_clima.consultar_clima(-22.9, -47.06)
    modulo_clima.consultar_clima(-22.9, -47.06)
    assert len(rede["chamadas"]) == 1


def test_coordenadas_proximas_compartilham_a_mesma_chave_de_cache(rede):
    modulo_clima.consultar_clima(-22.9012, -47.0608)
    modulo_clima.consultar_clima(-22.9049, -47.0611)  # ambas arredondam para (-22.90, -47.06)
    assert len(rede["chamadas"]) == 1


def test_coordenadas_distantes_nao_compartilham_cache(rede):
    modulo_clima.consultar_clima(-22.90, -47.06)
    modulo_clima.consultar_clima(-23.55, -46.63)
    assert len(rede["chamadas"]) == 2


def test_cache_expirado_consulta_de_novo(rede, monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(modulo_clima.time, "time", lambda: agora[0])
    modulo_clima.consultar_clima(-22.9, -47.06)
    agora[0] += modulo_clima.TTL_CACHE_SEGUNDOS - 1
    modulo_clima.consultar_clima(-22.9, -47.06)
    assert len(rede["chamadas"]) == 1
    agora[0] += 2
    modulo_clima.consultar_clima(-22.9, -47.06)
    assert len(rede["chamadas"]) == 2


@pytest.mark.parametrize("campo", list(RESPOSTA_BOA["current"]))
def test_campo_ausente_ou_nulo_devolve_indisponivel(rede, campo):
    rede["resposta"] = RespostaFalsa(corpo(**{campo: None}))
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is False


def test_resposta_sem_bloco_current_devolve_indisponivel(rede):
    rede["resposta"] = RespostaFalsa({})
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is False


@pytest.mark.parametrize("campos", [dict(temperature_2m=200), dict(temperature_2m=-80),
                                    dict(relative_humidity_2m=101), dict(relative_humidity_2m=-1),
                                    dict(wind_speed_10m=-3), dict(precipitation=-0.5)])
def test_valores_fisicamente_impossiveis_sao_rejeitados(rede, campos):
    rede["resposta"] = RespostaFalsa(corpo(**campos))
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is False


@pytest.mark.parametrize("status", [400, 404, 429, 500, 503])
def test_status_http_de_erro_devolve_indisponivel(rede, status):
    rede["resposta"] = RespostaFalsa(RESPOSTA_BOA, status_code=status)
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is False


def test_excecao_de_rede_nao_quebra_o_sistema(rede):
    rede["erro"] = TimeoutError("sem internet")
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is False


def test_falha_nao_e_guardada_no_cache(rede):
    rede["erro"] = TimeoutError("sem internet")
    modulo_clima.consultar_clima(-22.9, -47.06)
    rede["erro"] = None
    assert modulo_clima.consultar_clima(-22.9, -47.06).dados_confiaveis is True
    assert len(rede["chamadas"]) == 2


def test_clima_indisponivel_e_marcado_como_nao_confiavel():
    c = modulo_clima.obter_clima_indisponivel()
    assert c.dados_confiaveis is False


def test_clima_indisponivel_faz_o_motor_cair_em_amarelo():
    from backend.app.motor.regras import avaliar_abertura_segura
    from backend.app.motor.tipos import Semaforo
    resultado = avaliar_abertura_segura(modulo_clima.obter_clima_indisponivel())
    assert resultado.semaforo == Semaforo.AMARELO and resultado.disparou is False
