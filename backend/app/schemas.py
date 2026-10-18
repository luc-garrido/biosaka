# Esse cara vai ser o segurança da porta da API
from pydantic import BaseModel, Field 
from datetime import datetime 
from typing import Optional
from enum import Enum

class TipoManejo(str, Enum):
    ALIMENTACAO = "ALIMENTACAO"
    COLHEITA = "COLHEITA"
    REVISAO = "REVISAO"
    OUTRO = "OUTRO"

# Leitura da Colmeia

class ColmeiaInput(BaseModel):
    # Aqui nos não fazemos como um POO normal pq o pydantic ja faz isso e muito mais com o BaseModel
    nome: str = Field(..., examples = ["Colmeia 1 - Matriz"])
    localizacao: str = Field(...)
    peso_tara_kg: float = Field(..., examples = [4.5])
    especie_abelha: str = Field(..., examples = ["Apis Mellifera"])
    observacoes: Optional[str] = Field(None, examples = ["Colmeia produtiva"])
    
class ColmeiaOutput(ColmeiaInput):
    id: int = Field(...,examples=[1])
    data_cadastro_colmeia: datetime = Field(default_factory=datetime.now)
    # Faz o python ler o que o banco manda 
    model_config = {"from_attributes":True}

# Leitura da Balança

class LeituraInput(BaseModel):
    colmeia_id: int = Field(..., examples=[1])
    peso_bruto: float = Field(..., examples=[32.5])
    data_leitura_peso: datetime = Field(default_factory=datetime.now)

class LeituraOutput(LeituraInput):
    id: int = Field(..., examples=[2])
    model_config = {"from_attributes":True}

# Status (Os dados vão chegar do regras.py)

class StatusOutput(BaseModel):
    colmeia_id: int = Field(..., examples = [1])
    semaforo: str = Field(..., examples=["VERDE", "AMARELO", "VERMELHO"])
    status_escrito: str = Field(..., examples=["Tudo tranquilo. A colmeia esta saudavel e com boas reservas"])
    peso_atual_kg: float = Field(..., examples = [27.5])
    data_avaliacao: datetime = Field(default_factory=datetime.now)
    model_config = {"from_attributes":True}

class ManejoInput(BaseModel):
    colmeia_id: int = Field(..., examples=[5])
    tipo_manejo: TipoManejo = Field(..., examples=[TipoManejo.ALIMENTACAO]) # Nesse campo acho melhor deixar opçoes e nao digitar 
    descricao: Optional[str] = Field(None, examples = ["Adição de núcleo"])
    data_manejo: datetime = Field(default_factory=datetime.now)
    delta_peso_esperado: Optional[float] = Field(None, examples = [2.5])
    
class ManejoOutput(ManejoInput):
    id: int = Field(..., examples = [4])
    model_config = {"from_attributes":True}
    