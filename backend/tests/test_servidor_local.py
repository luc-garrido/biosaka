"""Verifica a fronteira do console local sem depender do MySQL."""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from io import BytesIO

import pytest

from frontend.servidor import ServidorLocal


@pytest.fixture
def console_local():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ServidorLocal)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = f"127.0.0.1:{server.server_port}"

    def pedir(method, path, body=None, headers=None):
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        conn.request(method, path, body=body, headers={"Host": host, **(headers or {})})
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result
    try:
        yield pedir, host
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)


def test_encaminha_com_chave_so_no_servidor(console_local):
    pedir, host = console_local
    class Resposta:
        status = 200
        def read(self): return b'[{"codigo":"COL-001"}]'
        def __enter__(self): return self
        def __exit__(self, *args): pass
    with patch("frontend.servidor.API_TOKEN", "segredo-apenas-servidor"), patch("frontend.servidor.urlopen", return_value=Resposta()) as upstream:
        status, body = pedir("GET", "/api/colmeias?limite=1000")
        assert status == 200 and json.loads(body)[0]["codigo"] == "COL-001"
        request = upstream.call_args.args[0]
        assert request.full_url == "http://127.0.0.1:8000/colmeias?limite=1000"
        assert request.get_header("X-api-key") == "segredo-apenas-servidor"
        assert b"segredo-apenas-servidor" not in body
        payload = '{"codigo":"COL-002","apiario_id":1}'
        assert pedir("POST", "/api/colmeias", payload, {"Origin":"http://"+host,"Content-Type":"application/json"})[0] == 200
        assert upstream.call_args.args[0].data == payload.encode()


def test_rejeita_origem_host_e_operacoes_fora_do_escopo(console_local):
    pedir, host = console_local
    with patch("frontend.servidor.urlopen") as upstream:
        assert pedir("GET", "/api/colmeias", headers={"Host":"externo.example"})[0] == 403
        assert pedir("GET", "/api/colmeias", headers={"Origin":"https://externo.example"})[0] == 403
        assert pedir("GET", "/api/colmeias", headers={"Sec-Fetch-Site":"cross-site"})[0] == 403
        assert pedir("POST", "/api/colmeias", "{}", {"Content-Type":"application/json"})[0] == 403
        assert pedir("GET", "/api/usuarios")[0] == 404
        assert pedir("GET", "/api/apiarios/1")[0] == 404
        assert pedir("PUT", "/colmeias/1", "{}", {"Origin":"http://"+host})[0] == 404
        assert pedir("POST", "/api/colmeias", "{}", {"Origin":"http://"+host,"Content-Type":"text/plain"})[0] == 415
        assert pedir("POST", "/api/colmeias", "{}", {"Origin":"http://"+host,"Content-Type":"application/json","Content-Length":"70000"})[0] == 413
        upstream.assert_not_called()


def test_falha_da_api_e_duplicidade_sao_preservadas(console_local):
    pedir, host = console_local
    with patch("frontend.servidor.urlopen", side_effect=URLError("offline")):
        status, body = pedir("GET", "/api/colmeias")
        assert status == 503 and "API indisponível" in json.loads(body)["detail"]
    erro = HTTPError("http://127.0.0.1:8000/colmeias",409,"Conflict",{},BytesIO(b'{"detail":"Duplicado"}'))
    with patch("frontend.servidor.urlopen", side_effect=erro):
        status, body = pedir("POST", "/api/colmeias", "{}", {"Origin":"http://"+host,"Content-Type":"application/json"})
        assert status == 409 and json.loads(body)["detail"] == "Duplicado"
