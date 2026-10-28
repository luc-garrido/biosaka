"""Mapeamento das seis tabelas. DDL oficial em database/v3/."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, create_engine, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, ENUM, INTEGER, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"init_command": "SET time_zone = '+00:00'"})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(16), unique=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Apiario(Base):
    __tablename__ = "apiarios"
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    nome: Mapped[str] = mapped_column(String(120))
    localizacao: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Colmeia(Base):
    __tablename__ = "colmeias"
    __table_args__ = (UniqueConstraint("apiario_id", "codigo"), CheckConstraint("peso_tara_kg IS NULL OR peso_tara_kg >= 0"))
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    apiario_id: Mapped[int] = mapped_column(ForeignKey("apiarios.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    codigo: Mapped[str] = mapped_column(String(50))
    data_instalacao: Mapped[date | None] = mapped_column(Date)
    situacao: Mapped[str] = mapped_column(ENUM("ativa", "em_observacao", "inativa"), server_default="ativa")
    especie_abelha: Mapped[str | None] = mapped_column(String(80))
    origem_rainha: Mapped[str | None] = mapped_column(String(120))
    data_introducao_rainha: Mapped[date | None] = mapped_column(Date)
    peso_tara_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Inspecao(Base):
    __tablename__ = "inspecoes"
    __table_args__ = (Index("idx_inspecoes_colmeia_data", "colmeia_id", "data_inspecao", "id"),)
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    colmeia_id: Mapped[int] = mapped_column(ForeignKey("colmeias.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    data_inspecao: Mapped[date] = mapped_column(Date)
    forca_enxame: Mapped[str] = mapped_column(ENUM("fraca", "media", "forte", "nao_avaliada"), server_default="nao_avaliada")
    postura: Mapped[str] = mapped_column(ENUM("observada", "nao_observada", "nao_avaliada"), server_default="nao_avaliada")
    reserva_alimentar: Mapped[str] = mapped_column(ENUM("baixa", "adequada", "nao_avaliada"), server_default="nao_avaliada")
    observacoes: Mapped[str] = mapped_column(String(2000), server_default="")
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class SerieDataset(Base):
    __tablename__ = "series_dataset"
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    colmeia_id: Mapped[int] = mapped_column(ForeignKey("colmeias.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    codigo: Mapped[str] = mapped_column(String(100), unique=True)
    metrica: Mapped[str] = mapped_column(ENUM("weight", "temperature", "humidity", "flow"))
    fonte_url: Mapped[str] = mapped_column(String(500))
    arquivo_origem: Mapped[str] = mapped_column(String(255))
    sha256_arquivo: Mapped[str] = mapped_column(CHAR(64))
    unidade_original: Mapped[str | None] = mapped_column(String(40))
    fuso_original: Mapped[str | None] = mapped_column(String(64))
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Leitura(Base):
    __tablename__ = "leituras"
    __table_args__ = (UniqueConstraint("serie_id", "linha_origem"),
                      Index("idx_leituras_serie_instante", "serie_id", "instante_original", "id"),
                      CheckConstraint("linha_origem >= 2"))
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    serie_id: Mapped[int] = mapped_column(ForeignKey("series_dataset.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    instante_original: Mapped[datetime] = mapped_column(DateTime)
    valor_original: Mapped[Decimal | None] = mapped_column(Numeric(24, 12))
    texto_valor_original: Mapped[str | None] = mapped_column(String(100))
    linha_origem: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    importado_em: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


def get_db():
    with SessionLocal() as db:
        yield db
