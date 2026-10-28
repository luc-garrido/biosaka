"""Cada execucao usa um schema MySQL temporario, nunca o banco do dataset."""
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / "database/v3/.env")
NOME_TESTE = "biosaka_test_" + uuid.uuid4().hex[:12]
os.environ["BIOSAKA_DB_NAME"] = NOME_TESTE


def sql_root(sql):
    resultado = subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "database/v3/compose.yaml"),
         "exec", "-T", "mysql", "sh", "-c",
         'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --default-character-set=utf8mb4 --batch'],
        input=sql, text=True, capture_output=True, timeout=30,
    )
    if resultado.returncode:
        raise RuntimeError(resultado.stderr)


@pytest.fixture(scope="session")
def client():
    assert re.fullmatch(r"biosaka_test_[0-9a-f]{12}", NOME_TESTE)
    scripts = "\n".join((ROOT / "database/v3" / nome).read_text(encoding="utf-8")
                        for nome in ("01_cadastros.sql", "02_medicoes.sql"))
    sql_root(f"CREATE DATABASE {NOME_TESTE} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;\n"
             f"GRANT ALL ON {NOME_TESTE}.* TO 'biosaka'@'%';\nUSE {NOME_TESTE};\n" + scripts)
    from fastapi.testclient import TestClient
    from backend.app.banco import engine
    from backend.app.main import site
    try:
        with TestClient(site, headers={"X-API-Key": os.environ["BIOSAKA_API_TOKEN"]}) as sessao:
            yield sessao
    finally:
        engine.dispose()
        sql_root(f"DROP DATABASE {NOME_TESTE};")


@pytest.fixture
def colmeia(client):
    telefone = "+999" + str(int(uuid.uuid4().hex[:8], 16)).zfill(10)
    usuario = client.post("/usuarios", json={"nome": "Teste", "telefone": telefone,
                                            "senha": "senha-ficticia-de-teste"})
    assert usuario.status_code == 201, usuario.text
    assert "senha" not in usuario.json() and "senha_hash" not in usuario.json()
    apiario = client.post("/apiarios", json={"usuario_id": usuario.json()["id"], "nome": "Teste"})
    assert apiario.status_code == 201, apiario.text
    dados = {"apiario_id": apiario.json()["id"], "codigo": "CX-01", "peso_tara_kg": "4.125"}
    resposta = client.post("/colmeias", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()
