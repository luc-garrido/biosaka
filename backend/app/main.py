from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .config import CORS_ORIGINS
from .rotas import roteador

site = FastAPI(title="BIOSAKA API", version="0.3.0",
               description="API administrativa local. Seis tabelas, MySQL e Beehive Metrics.")
site.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                    allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"],
                    allow_headers=["Content-Type", "X-API-Key"])
site.include_router(roteador)
app = site


@site.exception_handler(IntegrityError)
async def conflito(request: Request, erro: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Registro duplicado ou possui dependencias. Confira os relacionamentos."})


@site.exception_handler(SQLAlchemyError)
async def banco_indisponivel(request: Request, erro: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "Banco indisponivel ou esquema incompativel. Confira a configuracao e database/v3/."})
