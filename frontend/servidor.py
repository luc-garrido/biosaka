"""Serve a demonstração local sem enviar a chave administrativa ao navegador."""
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from dotenv import load_dotenv

FRONTEND = Path(__file__).resolve().parent
load_dotenv(FRONTEND.parent / "database/v3/.env")
API_TOKEN = os.environ["BIOSAKA_API_TOKEN"]
if len(API_TOKEN) < 32:
    raise ValueError("Configure BIOSAKA_API_TOKEN no .env local.")


class ServidorLocal(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def responder(self, status, corpo):
        if not isinstance(corpo, bytes):
            corpo = json.dumps({"detail": corpo}, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def host_local(self):
        hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in hosts:
            self.responder(403, "Acesso permitido apenas pelo endereço local.")
            return False
        return True

    def do_GET(self):
        if urlsplit(self.path).path.startswith("/api/"):
            self.encaminhar()
        elif self.host_local():
            super().do_GET()

    def encaminhar(self):
        if not self.host_local():
            return
        origem = "http://" + self.headers["Host"]
        if (self.headers.get("Origin", origem) != origem
                or self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none")
                or (self.command != "GET" and self.headers.get("Origin") != origem)):
            return self.responder(403, "Requisição deve partir da demonstração local.")
        url = urlsplit(self.path)
        if not url.path.startswith("/api/") or url.scheme or url.netloc:
            return self.responder(404, "Operação não disponível na demonstração.")
        caminho = url.path.removeprefix("/api")
        if not self.permitida(caminho):
            return self.responder(404, "Operação não disponível na demonstração.")
        publica = self.command == "POST" and caminho in ("/auth/login", "/usuarios")
        autorizacao = self.headers.get("Authorization", "")
        if not publica and not re.fullmatch(r"Bearer [A-Za-z0-9_\-.]{20,2048}", autorizacao):
            return self.responder(401, "Entre na sua conta para continuar.")
        corpo = None
        if self.command != "GET":
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.responder(415, "Envie JSON.")
            try:
                tamanho = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.responder(400, "Tamanho inválido.")
            if not 0 < tamanho <= 65536:
                return self.responder(413, "Corpo ausente ou muito grande.")
            corpo = self.rfile.read(tamanho)
        destino = "http://127.0.0.1:8000" + caminho + ("?" + url.query if url.query else "")
        cabecalhos = {"X-API-Key": API_TOKEN, "Content-Type": "application/json"}
        if not publica:
            cabecalhos["Authorization"] = autorizacao
        pedido = Request(destino, data=corpo, method=self.command, headers=cabecalhos)
        try:
            with urlopen(pedido, timeout=15) as resposta:
                self.responder(resposta.status, resposta.read())
        except HTTPError as erro:
            self.responder(erro.code, erro.read())
        except (URLError, TimeoutError):
            self.responder(503, "API indisponível. Confira o servidor na porta 8000.")

    ROTAS = {
        "GET": (r"/apiarios", r"/colmeias", r"/colmeias/\d+", r"/colmeias/\d+/diagnostico",
                r"/inspecoes", r"/series", r"/series/\d+/leituras"),
        "POST": (r"/auth/login", r"/usuarios", r"/apiarios", r"/colmeias", r"/inspecoes"),
        "PUT": (r"/colmeias/\d+",),
    }

    def permitida(self, caminho):
        return any(re.fullmatch(rota, caminho) for rota in self.ROTAS.get(self.command, ()))

    do_POST = encaminhar
    do_PUT = encaminhar


if __name__ == "__main__":
    # O navegador nunca recebe a chave administrativa; cada pedido de dados exige o token do login.
    print("Demonstração local: http://127.0.0.1:5173/login.html")
    ThreadingHTTPServer(("127.0.0.1", 5173), ServidorLocal).serve_forever()
