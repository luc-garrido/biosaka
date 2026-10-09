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


# --- Modelos de Dados ---
class CriarColmeia(BaseModel):
    nome: str = Field(..., examples=["Colmeia 01 - Matriz"])
    localizacao: str = Field(..., examples=["Apiário Setor Norte"])
    peso_tara_kg: float = Field(...)
    data_introducao_rainha: str = Field(...)


class LerColmeia(BaseModel):
    colmeia_id: int = Field(..., examples=[1])
    peso: float = Field(..., examples=[26.7], description="Peso da caixa em kg")


# --- Banco de dados em memória temporário para testes ---
colmeias_db = []


# --- Rotas da API ---
@site.get("/")
def verificar_status():
    return {
        "status": "online",
        "projeto": "Biosoka API",
    }


@site.post("/colmeias", status_code=status.HTTP_201_CREATED)
def cadastrar_colmeia(dados: CriarColmeia):
    novo_id = len(colmeias_db) + 1
    nova_colmeia = {
        "colmeia_id": novo_id,
        "nome": dados.nome,
        "localizacao": dados.localizacao,
        "peso": 0.0
    }
    colmeias_db.append(nova_colmeia)
    return nova_colmeia


@site.get("/colmeias")
def listar_colmeias():
    return colmeias_db


# --- Inicializador do Servidor ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:site", host="127.0.0.1", port=8000, reload=True)
