"""Problemas e pendencias conhecidos, registrados como testes esperados-a-falhar.

Cada teste descreve o comportamento CORRETO. Hoje ele falha (xfail), entao a suite
continua verde, mas o problema fica documentado e rastreavel. xfail estrito: quando
o ajuste for feito o teste passa de repente, o pytest acusa XPASS(strict) e basta
remover a marca @pytest.mark.xfail para ele virar um teste normal.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pendente = lambda motivo: pytest.mark.xfail(strict=True, reason=motivo)  # noqa: E731


@pendente("semaforo.py escolhe a frase pela COR da RF03, nao pela causa: com dados "
          "insuficientes da balanca o usuario le 'melgueira em enchimento ativo'.")
def test_sem_dados_da_balanca_a_frase_nao_fala_em_enchimento_de_melgueira():
    from backend.app.motor.regras import avaliar_todas_regras
    from backend.app.motor.semaforo import consolidar_diagnostico
    from backend.app.motor.tipos import ContextoClima, FeaturesSinal
    sem_leituras = FeaturesSinal(0.0, None, None, False, 0.0, dados_suficientes=False,
                                 tara_definida=True, possui_leituras=False)
    clima_ideal = ContextoClima(25.0, False, 5.0, True, 50.0)
    frase = consolidar_diagnostico(avaliar_todas_regras(sem_leituras, clima_ideal)).frase_modo_avo
    assert "enchimento" not in frase and "maturação" not in frase


@pendente("O frontend (localStorage) envia usuario/cidade/estado/pais, telefone no formato "
          "(11) 91234-5678 e senha de 6 caracteres; a API exige nome, telefone +E.164, senha de 8+ "
          "e rejeita campos extras.")
def test_cadastro_no_formato_do_frontend_e_aceito_pela_api(client):
    corpo = {"usuario": "apicultor1", "email": "apicultor1@example.com",
             "telefone": "(19) 91234-5678", "cidade": "Campinas", "estado": "São Paulo",
             "pais": "Brasil", "senha": "abc123"}
    assert client.post("/usuarios", json=corpo).status_code == 201


def test_existe_rota_de_login_na_api(client):
    caminhos = client.get("/openapi.json").json()["paths"]
    assert any("login" in c or "token" in c for c in caminhos)


def test_existe_rota_que_expoe_o_diagnostico_da_colmeia(client):
    caminhos = client.get("/openapi.json").json()["paths"]
    assert any("diagnostico" in c or "semaforo" in c for c in caminhos)


@pendente("clima.consultar_clima precisa de latitude/longitude, mas o modelo de apiario so "
          "guarda 'localizacao' em texto livre.")
def test_apiario_guarda_coordenadas_para_consultar_o_clima():
    from backend.app.schemas import ApiarioInput
    assert {"latitude", "longitude"} <= set(ApiarioInput.model_fields)


def test_env_example_so_tem_valores_modelo():
    linhas = (ROOT / "database/v3/.env.example").read_text(encoding="utf-8").splitlines()
    valores = {}
    repetidas = []
    for linha in linhas:
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            if chave in valores:
                repetidas.append(chave)
            valores[chave] = valor
    assert not repetidas
    assert all(valor.startswith("gere_") for valor in valores.values())
