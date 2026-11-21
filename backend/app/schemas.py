from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

ID = Annotated[int, Field(gt=0, strict=True)]
Nome = Annotated[str, Field(min_length=1, max_length=120)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class UsuarioInput(Entrada):
    nome: Nome
    telefone: Annotated[str, Field(pattern=r"^\+[1-9][0-9]{7,14}$")]
    email: EmailStr | None = None
    senha: SecretStr = Field(min_length=8, max_length=128)


class UsuarioOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    telefone: str
    email: str | None


class ApiarioInput(Entrada):
    usuario_id: ID
    nome: Nome
    localizacao: Annotated[str, Field(max_length=255)] | None = None


class ApiarioOutput(ApiarioInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ColmeiaInput(Entrada):
    apiario_id: ID
    codigo: Annotated[str, Field(min_length=1, max_length=50)]
    data_instalacao: date | None = None
    situacao: Literal["ativa", "em_observacao", "inativa"] = "ativa"
    especie_abelha: Annotated[str, Field(max_length=80)] | None = None
    origem_rainha: Annotated[str, Field(max_length=120)] | None = None
    data_introducao_rainha: date | None = None
    peso_tara_kg: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=3)] | None = None


class ColmeiaOutput(ColmeiaInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InspecaoInput(Entrada):
    colmeia_id: ID
    data_inspecao: date
    forca_enxame: Literal["fraca", "media", "forte", "nao_avaliada"] = "nao_avaliada"
    postura: Literal["observada", "nao_observada", "nao_avaliada"] = "nao_avaliada"
    reserva_alimentar: Literal["baixa", "adequada", "nao_avaliada"] = "nao_avaliada"
    observacoes: Annotated[str, Field(max_length=2000)] = ""

    @field_validator("data_inspecao")
    @classmethod
    def rejeitar_futuro(cls, valor):
        if valor > date.today():
            raise ValueError("Data de inspecao nao pode estar no futuro.")
        return valor


class InspecaoOutput(InspecaoInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SerieOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    colmeia_id: int
    codigo: str
    metrica: str
    fonte_url: str
    arquivo_origem: str
    sha256_arquivo: str
    unidade_original: str | None
    fuso_original: str | None


class LeituraOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    serie_id: int
    instante_original: datetime
    valor_original: Decimal | None
    texto_valor_original: str | None
    linha_origem: int


class PaginaLeituras(BaseModel):
    serie: SerieOutput
    total: int
    limite: int
    offset: int
    itens: list[LeituraOutput]

class LoginInput(Entrada):
    email: EmailStr
    senha: SecretStr = Field(min_length=8, max_length=128)


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
