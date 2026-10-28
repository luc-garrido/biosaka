from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .banco import Usuario, get_db
from .config import API_TOKEN

JWT_SECRET: str = API_TOKEN
JWT_ALGORITMO: str = "HS256"
TOKEN_MINUTOS: int = 30
EMISSOR_JWT: str = "biosaka"
AUDIENCIA_JWT: str = "biosaka-api"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash(senha: str):
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, hash_salvo: str):
    return pwd_context.verify(senha_plana, hash_salvo)


def criar_token(usuario_id: int):
    agora = datetime.now(timezone.utc)

    Conteudo = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=30),
        "iss": "biosaka",
        "aud": "biosaka-api",
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
