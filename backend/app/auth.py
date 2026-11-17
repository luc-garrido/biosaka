"""Login com e-mail e senha e token JWT de curta duracao."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from .banco import Usuario, get_db
from .config import API_TOKEN

JWT_SECRET: str = API_TOKEN
JWT_ALGORITMO: str = "HS256"
TOKEN_MINUTOS: int = 30
EMISSOR_JWT: str = "biosaka"
AUDIENCIA_JWT: str = "biosaka-api"


def gerar_hash(senha: str) -> str:
    """Mesmo formato gravado por POST /usuarios: scrypt$n$r$p$salt$digest."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(senha.encode(), salt=salt, n=16384, r=8, p=1)
    return "scrypt$16384$8$1$" + salt.hex() + "$" + digest.hex()


def verificar_senha(senha_plana: str, hash_salvo: str) -> bool:
    try:
        nome, n, r, p, salt, digest = hash_salvo.split("$")
        if nome != "scrypt":
            return False
        calculado = hashlib.scrypt(senha_plana.encode(), salt=bytes.fromhex(salt),
                                   n=int(n), r=int(r), p=int(p))
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(calculado.hex(), digest)


def criar_token(usuario_id: int) -> str:
    agora = datetime.now(timezone.utc)
    conteudo = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=TOKEN_MINUTOS),
        "iss": EMISSOR_JWT,
        "aud": AUDIENCIA_JWT,
    }
    return jwt.encode(conteudo, JWT_SECRET, algorithm=JWT_ALGORITMO)


bearer = HTTPBearer(auto_error=False)


def usuario_atual(db: Session = Depends(get_db), credenciais=Depends(bearer)):
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessao expirada ou token invalido. Entre novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credenciais is None:
        raise erro
    try:
        dados = jwt.decode(
            credenciais.credentials, JWT_SECRET, algorithms=[JWT_ALGORITMO],
            issuer=EMISSOR_JWT, audience=AUDIENCIA_JWT,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
        usuario_id = int(dados["sub"])
        if not 0 < usuario_id < 2**64:
            raise ValueError("Identificador invalido.")
    except (jwt.PyJWTError, ValueError, TypeError):
        raise erro
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise erro
    return usuario


def token_se_enviado(db: Session = Depends(get_db), credenciais=Depends(bearer)):
    """Se o pedido trouxer Authorization: Bearer, o token precisa ser valido."""
    if credenciais is not None:
        usuario_atual(db, credenciais)
