import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from .banco import Usuario, get_db
from .config import JWT_SECRET

JWT_ALGORITMO: str = "HS256"
TOKEN_MINUTOS: int = 30
EMISSOR_JWT: str = "biosaka"
AUDIENCIA_JWT: str = "biosaka-api"

SCRYPT_N, SCRYPT_R, SCRYPT_P = 16384, 8, 1


def gerar_hash(senha: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(senha.encode(), salt=salt,
                            n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verificar_senha(senha: str, hash_salvo: str | None) -> bool:
    if not hash_salvo or not hash_salvo.startswith("scrypt$"):
        return False
    try:
        _, n, r, p, salt, digest = hash_salvo.split("$")
        calc = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(salt),
                              n=int(n), r=int(r), p=int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calc.hex(), digest)


HASH_FALSO = gerar_hash(secrets.token_urlsafe(16))


def criar_token(usuario_id: int):
    agora = datetime.now(timezone.utc)

    Conteudo = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=TOKEN_MINUTOS),
        "iss": EMISSOR_JWT,
        "aud": AUDIENCIA_JWT,
    }

    return jwt.encode(Conteudo, JWT_SECRET, algorithm=JWT_ALGORITMO)


bearer = HTTPBearer(auto_error=False)


def usuario_atual(db: Session = Depends(get_db), credenciais=Depends(bearer)):

    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticação necessária ou token inválido.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciais is None:
        raise erro

    try:
        dados = jwt.decode(
            credenciais.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITMO],
            issuer=EMISSOR_JWT,
            audience=AUDIENCIA_JWT,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
        usuario_id = int(dados["sub"])

        if not 0 < usuario_id < 2**64:
            raise ValueError("Identificador inválido.")
    except (jwt.PyJWTError, ValueError, TypeError):
        raise erro

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise erro

    return usuario


UsuarioAutenticado = Annotated[Usuario, Depends(usuario_atual)]
