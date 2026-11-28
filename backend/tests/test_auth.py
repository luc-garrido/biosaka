"""Testes de senha (scrypt) e de token JWT.

A dependencia usuario_atual consulta o banco; por isso os testes de HTTP usam o
schema temporario criado pela fixture `client` (mesmo MySQL dos demais testes).
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import auth
from backend.app.config import JWT_SECRET


# --------------------------------------------------------------------------
# hash de senha
# --------------------------------------------------------------------------

def test_hash_confere_com_a_senha_certa_e_rejeita_a_errada():
    hash_salvo = auth.gerar_hash("senha-de-teste-123")
    assert auth.verificar_senha("senha-de-teste-123", hash_salvo) is True
    assert auth.verificar_senha("senha-de-teste-124", hash_salvo) is False


def test_hash_nao_contem_a_senha_e_usa_formato_scrypt():
    hash_salvo = auth.gerar_hash("senha-de-teste-123")
    assert "senha-de-teste-123" not in hash_salvo
    assert hash_salvo.startswith("scrypt$16384$8$1$") and len(hash_salvo.split("$")) == 6


def test_mesma_senha_gera_hashes_diferentes_por_causa_do_sal():
    assert auth.gerar_hash("igual-igual") != auth.gerar_hash("igual-igual")


@pytest.mark.parametrize("hash_invalido", [None, "", "texto-qualquer", "bcrypt$abc",
                                          "scrypt$16384$8$1$zz$zz", "scrypt$x$8$1$00$00",
                                          "scrypt$16384$8$1$00"])
def test_hash_ausente_ou_malformado_nunca_autentica(hash_invalido):
    assert auth.verificar_senha("qualquer-senha", hash_invalido) is False


def test_senha_com_acentos_e_emoji_funciona():
    hash_salvo = auth.gerar_hash("abelhão-🐝-çedilha")
    assert auth.verificar_senha("abelhão-🐝-çedilha", hash_salvo) is True


def test_hash_falso_existe_para_igualar_o_tempo_de_login_de_usuario_inexistente():
    assert auth.HASH_FALSO.startswith("scrypt$")
    assert auth.verificar_senha("qualquer", auth.HASH_FALSO) is False


# --------------------------------------------------------------------------
# criacao do token
# --------------------------------------------------------------------------

def decodificar(token):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="biosaka-api", issuer="biosaka")


def test_token_traz_as_claims_esperadas_e_expira_em_30_minutos():
    dados = decodificar(auth.criar_token(42))
    assert dados["sub"] == "42" and dados["iss"] == "biosaka" and dados["aud"] == "biosaka-api"
    assert dados["exp"] - dados["iat"] == 30 * 60


# --------------------------------------------------------------------------
# dependencia usuario_atual (HTTP + banco)
# --------------------------------------------------------------------------

@pytest.fixture
def app_protegida(client):
    app = FastAPI()

    @app.get("/eu")
    def eu(usuario: auth.UsuarioAutenticado):
        return {"id": usuario.id, "telefone": usuario.telefone}

    return TestClient(app)


@pytest.fixture
def usuario_id(colmeia):
    from backend.app.banco import Apiario, SessionLocal
    with SessionLocal() as db:
        return db.get(Apiario, colmeia["apiario_id"]).usuario_id


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def token_manual(**mudancas):
    agora = datetime.now(timezone.utc)
    claims = {"sub": "1", "iat": agora, "exp": agora + timedelta(minutes=5),
              "iss": "biosaka", "aud": "biosaka-api"}
    claims.update(mudancas)
    return claims


def test_token_valido_de_usuario_existente_e_aceito(app_protegida, usuario_id):
    resposta = app_protegida.get("/eu", headers=cabecalho(auth.criar_token(usuario_id)))
    assert resposta.status_code == 200 and resposta.json()["id"] == usuario_id


def test_sem_credencial_responde_401_com_www_authenticate(app_protegida):
    resposta = app_protegida.get("/eu")
    assert resposta.status_code == 401 and resposta.headers["www-authenticate"] == "Bearer"


def test_token_lixo_e_rejeitado(app_protegida):
    assert app_protegida.get("/eu", headers=cabecalho("isto.nao.e.jwt")).status_code == 401


def test_token_expirado_e_rejeitado(app_protegida, usuario_id):
    agora = datetime.now(timezone.utc)
    token = jwt.encode(token_manual(sub=str(usuario_id), iat=agora - timedelta(hours=2),
                                    exp=agora - timedelta(hours=1)), JWT_SECRET, algorithm="HS256")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


def test_token_assinado_com_outra_chave_e_rejeitado(app_protegida, usuario_id):
    token = jwt.encode(token_manual(sub=str(usuario_id)), "x" * 40, algorithm="HS256")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


@pytest.mark.parametrize("mudanca", [dict(aud="outra-api"), dict(iss="outro-emissor")])
def test_audiencia_ou_emissor_errados_sao_rejeitados(app_protegida, usuario_id, mudanca):
    token = jwt.encode(token_manual(sub=str(usuario_id), **mudanca), JWT_SECRET, algorithm="HS256")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


def test_token_sem_algoritmo_none_e_rejeitado(app_protegida, usuario_id):
    token = jwt.encode(token_manual(sub=str(usuario_id)), key=None, algorithm="none")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


@pytest.mark.parametrize("claim", ["sub", "exp", "iat", "iss", "aud"])
def test_token_sem_claim_obrigatoria_e_rejeitado(app_protegida, usuario_id, claim):
    claims = token_manual(sub=str(usuario_id))
    del claims[claim]
    token = jwt.encode(claims, JWT_SECRET, algorithm="HS256")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


@pytest.mark.parametrize("sub", ["abc", "0", "-5", str(2**64), "1.5", ""])
def test_sub_invalido_e_rejeitado(app_protegida, sub):
    token = jwt.encode(token_manual(sub=sub), JWT_SECRET, algorithm="HS256")
    assert app_protegida.get("/eu", headers=cabecalho(token)).status_code == 401


def test_token_de_usuario_inexistente_e_rejeitado(app_protegida):
    assert app_protegida.get("/eu", headers=cabecalho(auth.criar_token(2**40))).status_code == 401
