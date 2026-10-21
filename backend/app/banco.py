"""
==============================================================================
ARQUIVO: app/banco.py
PAPEL: "A Despensa / O Livro de Registros Permanentes (MySQL via SQLAlchemy)"
==============================================================================

O QUE É ESTE ARQUIVO?
Este arquivo é a ponte entre a nossa aplicação Python e o servidor de banco de dados
MySQL. Ele usa o SQLAlchemy (um ORM - Object-Relational Mapper).

POR QUE ELE EXISTE SEPARADO?
Se você guardar informações apenas em variáveis Python normais, assim que o servidor
for desligado ou reiniciar, TUDO É PERDIDO.
Este arquivo garante que todas as colmeias cadastradas, pesos da balança e alertas
sejam gravados de forma segura e permanente no disco rígido do MySQL.

AS DUAS GRANDES PARTES DESTE ARQUIVO:

1. INFRAESTRUTURA DE CONEXÃO:
   - DATABASE_URL: O endereço no GPS com usuário, senha, porta e nome do banco.
   - engine: A "estrada/central telefônica" que gerencia as conexões físicas de rede.
   - SessionLocal: A "fábrica de atendimentos" (cada requisição ganha um rascunho de sessão).
   - get_db(): A função com 'yield' que empresta uma sessão aberta para a rota e garante
     que ela seja fechada no final, evitando travar o MySQL por falta de conexões.

2. MODELOS DE TABELA (Classes ORM):
   - Em vez de escrever comandos SQL crus ("CREATE TABLE colmeias ..."), criamos
     classes Python herdando de 'Base'.
   - O SQLAlchemy traduz essas classes em tabelas reais com chaves primárias e tipos.
==============================================================================
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, DECIMAL
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_URL = 'A URL do banco (Quando eu tiver acesso)'

engine = create_engine(DATABASE_URL)
# Abrir uma conexão de rede com o MySQL é um processo pesado e lento. O engine cria o que chamamos de Pool de Conexões: 
# ele mantém algumas conexões pré-aquecidas e abertas, gerenciando o tráfego pesado para que a API seja ultrarrápida.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 1. Não salva automaticamente a cada linha de código (autocommit=False)
# 2. Não envia comandos duplicados para o banco (autoflush=False)
# 3. Usa a conexão gerada pelo nosso engine (bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Colmeia(Base):
    __tablename__ = 'colmeias'

    id = Column(Integer, primary_key=True, index=True)
    apiario_id = Column(Integer, nullable=False)  
    codigo_identificacao = Column(String(20), nullable=False)  
    especie_abelha = Column(String(80), nullable=True)
    data_instalacao = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="ATIVA")
    peso_tara_kg = Column(Float, default=0.0)  

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)

class Apiario(Base):
    __tablename__ = 'apiarios'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    nome = Column(String(100), nullable=False)
    localizacao = Column(String(200))
    data_criacao = Column(DateTime, default=datetime.now)
    
class Inspecao(Base):
    __tablename__ = 'inspecoes'

    id = Column(Integer, primary_key=True, index=True)
    colmeia_id = Column(Integer, nullable=False)
    data_inspecao = Column(DateTime, default=datetime.now)
    peso_kg = Column(DECIMAL(5,2), nullable=False)
    presenca_rainha = Column(Boolean, default=True)
    nivel_populacao = Column(String(20), default='ALTO')
    reserva_alimento = Column(String(20), default='SUFICIENTE')
    sinais_pragas = Column(Boolean, default=False)
    observacoes = Column(Text)

class Alerta(Base):
    __tablename__ = 'alertas'

    id = Column(Integer, primary_key=True, index=True)
    colmeia_id = Column(Integer, nullable=False)
    tipo_alerta = Column(String(50), nullable=False)
    descricao = Column(String(255), nullable=False) 
    gravidade = Column(String(20), default='MEDIA')
    data_criacao = Column(DateTime, default=datetime.now)
    resolvido = Column(Boolean, default=False)   