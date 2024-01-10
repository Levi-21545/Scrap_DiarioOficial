from db_config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

# Configurar a conexão com o banco de dados
engine = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

class DiarioItem(Base):
    __tablename__ = 'servidores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_func = Column(String(10), nullable=False)
    nome = Column(String(60), nullable=False)
    materia = Column(Integer, nullable=False)
    data = Column(Date, nullable=False)
    tipo_vinculo = Column(String(30), nullable=True)
    cargo_funcao = Column(String(255), nullable=True)

    def __init__(self, id_func, nome, materia, data, tipo_vinculo, cargo_funcao):
        self.id_func = id_func
        self.nome = nome
        self.materia = materia
        self.data = data
        self.tipo_vinculo = tipo_vinculo
        self.cargo_funcao = cargo_funcao


def connect_database():
    # Configurar a conexão com o banco de dados
    engine = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()