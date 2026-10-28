"""
==============================================================================
ARQUIVO: app/rotas.py
PAPEL: "O Balcão de Atendimento / Os Endpoints HTTP da API"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo define as URLs da sua API. Ele é a única camada que "fala a língua
da Web" (o protocolo HTTP com GET, POST, PUT, DELETE).

POR QUE ELE EXISTE SEPARADO?
O papel de uma rota é ser simples e direta:
1. Receber a requisição que veio pela internet (do frontend ou do ESP32).
2. Usar os contratos de 'schemas.py' para validar se os dados estão certos.
3. Chamar a função correspondente em 'servicos.py' para fazer o trabalho pesado.
4. Responder com o status HTTP correto (200 OK, 201 Created, 404 Not Found).
A rota NÃO deve conter lógica matemática nem comandos SQL diretos.

AS ROTAS PRINCIPAIS DO BIOSAKA:
1. POST /leituras
   - Quem chama: A balança ESP32 enviando o peso medido em tempo real.
   - O que faz: Recebe o peso e dispara a avaliação de saúde da colmeia.

2. GET /colmeias
   - Quem chama: O aplicativo na tela inicial.
   - O que faz: Devolve a lista de todas as caixas cadastradas no apiário.

3. POST /colmeias
   - Quem chama: O apicultor cadastrando uma caixa nova no sistema.

4. POST /colmeias/{id}/manejo
   - Quem chama: O apicultor registrando uma ação de campo (colheu mel, alimentou).

5. GET /colmeias/{id}/status
   - Quem chama: A tela principal do "Modo Avô" no aplicativo.
   - O que faz: Devolve a cor do semáforo (Verde/Amarelo/Vermelho) e a frase de ação.
==============================================================================
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import Apiario, Colmeia, get_db
from schemas import (
    ColmeiaInput,
    ColmeiaOutput,
    LeituraInput,
    LeituraOutput,
    ManejoInput,
    ManejoOutput,
    Semaforo,
    StatusOutput,
)

def obter_colmeia_ou_404(db: Session, colmeia_id: int):
    colmeia = db.get(Colmeia, colmeia_id)
    if colmeia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Colmeia {colmeia_id} não encontrada")
    return colmeia

roteador = APIRouter()

#Status do sistema
@roteador.get("/", tags=["Sistema"])
def verificar_status():
   return {"status": "online", "projeto": "Biosaka API"}

#Cadastrar colmeia
@roteador.post("/colmeias", response_model=ColmeiaOutput, status_code=201, tags=["Colmeias"])
def cadastrar_colmeia(dados: ColmeiaInput, db: Session = Depends(get_db)):
   if db.get(Apiario, dados.apiario_id) is None:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail=f"Apiario {dados.apiario_id} não foi encontrado"
      )
   colmeia = Colmeia(**dados.model_dump())
   db.add(colmeia)
   db.commit()
   db.refresh(colmeia)
   return colmeia

#Listar todas as colmeias do apiário
#Att futura -> definir um limite de colmeias a aparecer
#o apicultor poderia decidir ? ou seria pré definido?
@roteador.get("/colmeias", response_model=list[ColmeiaOutput], tags=["Colmeias"])
def listar_colmeias(dados: ColmeiaInput, db: Session = Depends(get_db)):
   consulta = select(Colmeia)
   if dados.apiario_id is not None:
      consulta = consulta.where(Colmeia.apiario_id == dados.apiario_id)
   return db.scalars(consulta).all()

#Colmeia específica
@roteador.get("/colmeias/{colmeia_id}", response_model=ColmeiaOutput, tags=["Colmeias"])
def buscar_colmeia(colmeia_id: int, db: Session = Depends(get_db)):
    return obter_colmeia_ou_404(db, colmeia_id)

#Leitura do peso
@roteador.post("/leituras", response_model=LeituraOutput, 
               status_code=status.HTTP_201_CREATED, tags=["Leituras"],)
def receber_leitura(dados: LeituraInput, db: Session = Depends(get_db)):
    obter_colmeia_ou_404(db, dados.colmeia_id)
    # Converte os dados recebidos e trata a data/hora
    campos = dados.model_dump()
    #campos["data_hora"] = para_utc_naive(campos["data_hora"])    

    leitura = LeituraOutput(**campos)
    db.add(leitura)
    db.commit()
    db.refresh(leitura)
    return leitura

@roteador.post("/colmeias/{colmeia_id}/manejo", response_model=ManejoOutput, 
               status_code=201, tags=["Manejos"])
def registar_manejo(colmeia_id: int, dados:ManejoOutput, db: Session = Depends(get_db)):
   obter_colmeia_ou_404(db, colmeia_id)
   campos = dados.model_dump()

   manejo = ManejoOutput(colmeia_id=colmeia_id, **campos)
   db.add(manejo)
   db.commit()
   db.refresh(manejo)
   return manejo