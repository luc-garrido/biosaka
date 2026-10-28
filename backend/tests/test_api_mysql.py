from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select


def test_saude_verifica_seis_tabelas_reais(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["database_checked"] is True
    assert resposta.json()["tabelas"] == ["apiarios", "colmeias", "inspecoes", "leituras", "series_dataset", "usuarios"]


def test_chave_obrigatoria(client):
    assert client.get("/colmeias", headers={"X-API-Key": "invalida"}).status_code == 401
    assert client.get("/colmeias", headers={"X-API-Key": ""}).status_code == 401


def test_cadastro_edicao_e_listagem_sem_corpo_get(client, colmeia):
    resposta = client.get("/colmeias", params={"apiario_id": colmeia["apiario_id"]})
    assert resposta.status_code == 200 and resposta.json() == [colmeia]
    dados = {k: v for k, v in colmeia.items() if k != "id"}
    dados["situacao"] = "inativa"
    resposta = client.put(f"/colmeias/{colmeia['id']}", json=dados)
    assert resposta.status_code == 200, resposta.text
    assert client.get(f"/colmeias/{colmeia['id']}").json()["situacao"] == "inativa"
    assert client.post("/colmeias", json=dados).status_code == 409


def test_inspecoes_e_exclusoes_restritas(client, colmeia):
    dados = {"colmeia_id": colmeia["id"], "data_inspecao": "2017-01-01"}
    resposta = client.post("/inspecoes", json=dados)
    assert resposta.status_code == 201, resposta.text
    identificador = resposta.json()["id"]
    assert resposta.json()["postura"] == "nao_avaliada"
    assert client.get("/inspecoes", params={"colmeia_id": colmeia["id"]}).json()[0]["id"] == identificador
    assert client.delete(f"/colmeias/{colmeia['id']}").status_code == 409
    assert client.delete(f"/apiarios/{colmeia['apiario_id']}").status_code == 409
    assert client.put(f"/inspecoes/{identificador}", json={**dados, "reserva_alimentar": "baixa"}).status_code == 200
    assert client.delete(f"/inspecoes/{identificador}").status_code == 204
    assert client.delete(f"/colmeias/{colmeia['id']}").status_code == 204
    assert client.delete(f"/apiarios/{colmeia['apiario_id']}").status_code == 204


def test_validacoes_e_referencias(client, colmeia):
    dados = {"apiario_id": colmeia["apiario_id"], "codigo": "CX-02"}
    for extra in ({"peso_tara_kg": -1}, {"peso_tara_kg": "NaN"}, {"codigo": " "}, {"status": "ATIVA"}):
        assert client.post("/colmeias", json={**dados, **extra}).status_code == 422
    assert client.post("/colmeias", json={**dados, "apiario_id": 999999999}).status_code == 404
    assert client.post("/inspecoes", json={"colmeia_id": colmeia["id"],
        "data_inspecao": (date.today() + timedelta(days=1)).isoformat()}).status_code == 422
    assert client.get("/colmeias", params={"limite": 1001}).status_code == 422


def test_senha_e_telefone_unico(client, colmeia):
    from backend.app.banco import SessionLocal, Usuario, Apiario
    with SessionLocal() as db:
        apiario = db.get(Apiario, colmeia["apiario_id"])
        usuario = db.get(Usuario, apiario.usuario_id)
        assert usuario.senha_hash.startswith("scrypt$16384$8$1$")
        assert "senha-ficticia-de-teste" not in usuario.senha_hash
        telefone = usuario.telefone
    assert client.post("/usuarios", json={"nome": "Outro", "telefone": telefone,
                                           "senha": "outra-senha-teste"}).status_code == 409


def test_leituras_preservam_repeticoes_precisao_e_paginacao(client, colmeia):
    from backend.app.banco import Leitura, SerieDataset, SessionLocal
    from datetime import datetime
    with SessionLocal() as db:
        serie = SerieDataset(colmeia_id=colmeia["id"], codigo=f"teste-{colmeia['id']}",
            metrica="weight", fonte_url="https://example.invalid", arquivo_origem="teste.csv",
            sha256_arquivo="a" * 64, unidade_original="kg")
        db.add(serie)
        db.flush()
        for linha, valor in enumerate((Decimal("52.697400000001"), Decimal("-0.115216"), None), 2):
            db.add(Leitura(serie_id=serie.id, instante_original=datetime(2017, 1, 1, 5, 15),
                valor_original=valor, texto_valor_original=str(valor) if valor is not None else "",
                linha_origem=linha))
        db.commit()
        identificador = serie.id
    caminho = f"/series/{identificador}/leituras"
    resposta = client.get(caminho, params={"limite": 1, "offset": 1})
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["total"] == 3 and len(corpo["itens"]) == 1
    assert Decimal(corpo["itens"][0]["valor_original"]) == Decimal("-0.115216")
    assert corpo["serie"]["fuso_original"] is None
    assert client.get(caminho).json()["itens"][0]["valor_original"] == "52.697400000001"
    assert client.get(caminho, params={"inicio": "2017-01-02"}).json()["total"] == 0
    assert client.get(caminho, params={"inicio": "2017-01-02", "fim": "2017-01-01"}).status_code == 422
    assert client.get(caminho, params={"inicio": "2017-01-01T00:00:00Z"}).status_code == 422
    assert client.get("/series", params={"colmeia_id": colmeia["id"]}).json()[0]["id"] == identificador
    assert client.delete(f"/colmeias/{colmeia['id']}").status_code == 409
