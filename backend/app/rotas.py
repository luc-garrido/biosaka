import hashlib
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import APIKeyHeader
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from .banco import Apiario, Base, Colmeia, Inspecao, Leitura, SerieDataset, Usuario, get_db
from .config import API_TOKEN
from .schemas import (ApiarioInput, ApiarioOutput, ColmeiaInput, ColmeiaOutput,
                      InspecaoInput, InspecaoOutput, PaginaLeituras, SerieOutput,
                      UsuarioInput, UsuarioOutput)

cabecalho = APIKeyHeader(name="X-API-Key", auto_error=False)


def chave_local(chave: str | None = Depends(cabecalho)):
    # shortcut: chave administrativa local; substituir por identidade individual antes de oferecer acesso multiusuario.
    if chave is None or not secrets.compare_digest(chave.encode(), API_TOKEN.encode()):
        raise HTTPException(401, "Chave de acesso invalida.")


roteador = APIRouter(dependencies=[Depends(chave_local)])
DB = Annotated[Session, Depends(get_db)]
Limite = Annotated[int, Query(ge=1, le=1000)]
Offset = Annotated[int, Query(ge=0, le=10000000)]


def obter(db, modelo, identificador):
    registro = db.get(modelo, identificador)
    if registro is None:
        raise HTTPException(404, "Registro nao encontrado.")
    return registro


def salvar(db, registro):
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@roteador.get("/", include_in_schema=False)
@roteador.get("/health", tags=["Sistema"])
def health(db: DB):
    db.execute(text("SELECT 1"))
    inspetor = inspect(db.connection())
    tabelas = set(inspetor.get_table_names())
    if tabelas != set(Base.metadata.tables):
        raise HTTPException(503, "O banco deve conter somente as seis tabelas de database/v3/.")
    for nome, tabela in Base.metadata.tables.items():
        if {c["name"] for c in inspetor.get_columns(nome)} != set(tabela.columns.keys()):
            raise HTTPException(503, f"Estrutura incompativel na tabela {nome}.")
    return {"status": "ok", "database_checked": True, "tabelas": sorted(tabelas)}


@roteador.post("/usuarios", response_model=UsuarioOutput, status_code=201, tags=["Usuarios"])
def cadastrar_usuario(dados: UsuarioInput, db: DB):
    campos = dados.model_dump(exclude={"senha"})
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(dados.senha.get_secret_value().encode(), salt=salt, n=16384, r=8, p=1)
    campos["senha_hash"] = f"scrypt$16384$8$1$" + salt.hex() + "$" + digest.hex()
    return salvar(db, Usuario(**campos))


@roteador.get("/usuarios", response_model=list[UsuarioOutput], tags=["Usuarios"])
def listar_usuarios(db: DB, limite: Limite = 100, offset: Offset = 0):
    return db.scalars(select(Usuario).order_by(Usuario.id).limit(limite).offset(offset)).all()


@roteador.post("/apiarios", response_model=ApiarioOutput, status_code=201, tags=["Apiarios"])
def cadastrar_apiario(dados: ApiarioInput, db: DB):
    obter(db, Usuario, dados.usuario_id)
    return salvar(db, Apiario(**dados.model_dump()))


@roteador.get("/apiarios", response_model=list[ApiarioOutput], tags=["Apiarios"])
def listar_apiarios(db: DB, usuario_id: int | None = Query(None, gt=0),
                    limite: Limite = 100, offset: Offset = 0):
    consulta = select(Apiario)
    if usuario_id is not None:
        consulta = consulta.where(Apiario.usuario_id == usuario_id)
    return db.scalars(consulta.order_by(Apiario.id).limit(limite).offset(offset)).all()


@roteador.put("/apiarios/{apiario_id}", response_model=ApiarioOutput, tags=["Apiarios"])
def atualizar_apiario(apiario_id: int, dados: ApiarioInput, db: DB):
    registro = obter(db, Apiario, apiario_id)
    if registro.usuario_id != dados.usuario_id:
        raise HTTPException(409, "Nao e permitido transferir a propriedade do apiario.")
    for campo, valor in dados.model_dump().items():
        setattr(registro, campo, valor)
    return salvar(db, registro)


@roteador.delete("/apiarios/{apiario_id}", status_code=204, tags=["Apiarios"])
def excluir_apiario(apiario_id: int, db: DB):
    db.delete(obter(db, Apiario, apiario_id))
    db.commit()
    return Response(status_code=204)


@roteador.post("/colmeias", response_model=ColmeiaOutput, status_code=201, tags=["Colmeias"])
def cadastrar_colmeia(dados: ColmeiaInput, db: DB):
    obter(db, Apiario, dados.apiario_id)
    return salvar(db, Colmeia(**dados.model_dump()))


@roteador.get("/colmeias", response_model=list[ColmeiaOutput], tags=["Colmeias"])
def listar_colmeias(db: DB, apiario_id: int | None = Query(None, gt=0),
                    limite: Limite = 100, offset: Offset = 0):
    consulta = select(Colmeia)
    if apiario_id is not None:
        consulta = consulta.where(Colmeia.apiario_id == apiario_id)
    return db.scalars(consulta.order_by(Colmeia.id).limit(limite).offset(offset)).all()


@roteador.get("/colmeias/{colmeia_id}", response_model=ColmeiaOutput, tags=["Colmeias"])
def buscar_colmeia(colmeia_id: int, db: DB):
    return obter(db, Colmeia, colmeia_id)


@roteador.put("/colmeias/{colmeia_id}", response_model=ColmeiaOutput, tags=["Colmeias"])
def atualizar_colmeia(colmeia_id: int, dados: ColmeiaInput, db: DB):
    registro = obter(db, Colmeia, colmeia_id)
    if registro.apiario_id != dados.apiario_id:
        raise HTTPException(409, "Nao e permitido transferir uma colmeia com este endpoint.")
    for campo, valor in dados.model_dump().items():
        setattr(registro, campo, valor)
    return salvar(db, registro)


@roteador.delete("/colmeias/{colmeia_id}", status_code=204, tags=["Colmeias"])
def excluir_colmeia(colmeia_id: int, db: DB):
    db.delete(obter(db, Colmeia, colmeia_id))
    db.commit()
    return Response(status_code=204)


@roteador.post("/inspecoes", response_model=InspecaoOutput, status_code=201, tags=["Inspecoes"])
def registrar_inspecao(dados: InspecaoInput, db: DB):
    obter(db, Colmeia, dados.colmeia_id)
    return salvar(db, Inspecao(**dados.model_dump()))


@roteador.get("/inspecoes", response_model=list[InspecaoOutput], tags=["Inspecoes"])
def listar_inspecoes(db: DB, colmeia_id: int | None = Query(None, gt=0),
                     limite: Limite = 100, offset: Offset = 0):
    consulta = select(Inspecao)
    if colmeia_id is not None:
        consulta = consulta.where(Inspecao.colmeia_id == colmeia_id)
    return db.scalars(consulta.order_by(Inspecao.data_inspecao.desc(), Inspecao.id.desc())
                     .limit(limite).offset(offset)).all()


@roteador.put("/inspecoes/{inspecao_id}", response_model=InspecaoOutput, tags=["Inspecoes"])
def atualizar_inspecao(inspecao_id: int, dados: InspecaoInput, db: DB):
    registro = obter(db, Inspecao, inspecao_id)
    if registro.colmeia_id != dados.colmeia_id:
        raise HTTPException(409, "Nao e permitido transferir uma inspecao.")
    for campo, valor in dados.model_dump().items():
        setattr(registro, campo, valor)
    return salvar(db, registro)


@roteador.delete("/inspecoes/{inspecao_id}", status_code=204, tags=["Inspecoes"])
def excluir_inspecao(inspecao_id: int, db: DB):
    db.delete(obter(db, Inspecao, inspecao_id))
    db.commit()
    return Response(status_code=204)


@roteador.get("/series", response_model=list[SerieOutput], tags=["Dataset"])
def listar_series(db: DB, colmeia_id: int | None = Query(None, gt=0),
                   limite: Limite = 100, offset: Offset = 0):
    consulta = select(SerieDataset)
    if colmeia_id is not None:
        consulta = consulta.where(SerieDataset.colmeia_id == colmeia_id)
    return db.scalars(consulta.order_by(SerieDataset.id).limit(limite).offset(offset)).all()


@roteador.get("/series/{serie_id}/leituras", response_model=PaginaLeituras, tags=["Dataset"])
def consultar_leituras(serie_id: int, db: DB, inicio: datetime | None = None,
                        fim: datetime | None = None, limite: Limite = 100, offset: Offset = 0):
    serie = obter(db, SerieDataset, serie_id)
    if any(d is not None and d.tzinfo is not None for d in (inicio, fim)):
        raise HTTPException(422, "Use horarios originais sem fuso; o fuso do dataset nao esta confirmado.")
    if inicio is not None and fim is not None and fim < inicio:
        raise HTTPException(422, "Fim deve ser maior ou igual ao inicio.")
    filtros = [Leitura.serie_id == serie_id]
    if inicio is not None:
        filtros.append(Leitura.instante_original >= inicio)
    if fim is not None:
        filtros.append(Leitura.instante_original <= fim)
    total = db.scalar(select(func.count()).select_from(Leitura).where(*filtros))
    itens = db.scalars(select(Leitura).where(*filtros).order_by(
        Leitura.instante_original, Leitura.linha_origem, Leitura.id).limit(limite).offset(offset)).all()
    return {"serie": serie, "total": total, "limite": limite, "offset": offset, "itens": itens}
