from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

site = FastAPI(
    title="Biosaka API",
    description="Backend para monitoramento de colmeias",
    version="1.0.0"
)

site.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CriarColmeia(BaseModel):
    nome: str = Field(..., examples=["Colmeia 01 - Matriz"])
    localizacao: str = Field(..., examples=["Apiário Setor Norte"])


class LerColmeia(BaseModel):
    colmeia_id: int = Field(..., examples=[1])
    peso: float = Field(..., examples=[26.7],
                        description="Peso da caixa em kg")


@site.get("/")
def verificar_status():
    return {
        "status": "online",
        "projeto": "Biosoka API",
    }