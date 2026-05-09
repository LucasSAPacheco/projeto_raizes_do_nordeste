"""
Configuração dos testes: cria um banco de dados SQLite em memória
para que os testes rodem sem precisar do PostgreSQL instalado.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "chave-secreta-de-testes"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.infrastructure.database import Base, get_db
from app.domain.models import (
    Usuario, PerfilUsuario, Unidade, Produto,
    Estoque, PontosFidelidade
)
from app.infrastructure.security import hash_senha
from main import app

# Banco SQLite em memória só para testes
SQLITE_URL = "sqlite:///:memory:"
engine_teste = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

# SQLite não tem ENUMs nativos — usamos o modo string
@event.listens_for(engine_teste, "connect")
def set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

SessionTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


@pytest.fixture(scope="function")
def db():
    """Cria todas as tabelas, roda o teste e apaga tudo ao final."""
    Base.metadata.create_all(bind=engine_teste)
    session = SessionTeste()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture(scope="function")
def client(db):
    """Cliente HTTP para testar as rotas da API."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_cliente(db):
    """Cria um usuário cliente de exemplo para os testes."""
    usuario = Usuario(
        nome="João Teste",
        email="joao@teste.com",
        senha_hash=hash_senha("senha123"),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True,
    )
    db.add(usuario)
    db.flush()
    db.add(PontosFidelidade(usuario_id=usuario.id, saldo=0))
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def usuario_admin(db):
    """Cria um usuário admin de exemplo para os testes."""
    usuario = Usuario(
        nome="Admin Teste",
        email="admin@teste.com",
        senha_hash=hash_senha("admin123"),
        perfil=PerfilUsuario.ADMIN,
        consentimento_lgpd=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def unidade(db):
    """Cria uma unidade de exemplo para os testes."""
    u = Unidade(nome="Unidade Centro", endereco="Rua A, 1",
                cidade="Fortaleza", estado="CE")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def produto_com_estoque(db, unidade):
    """Cria um produto com estoque disponível na unidade."""
    produto = Produto(nome="Tapioca", preco=12.0, categoria="Lanche")
    db.add(produto)
    db.flush()
    estoque = Estoque(unidade_id=unidade.id, produto_id=produto.id, quantidade=10)
    db.add(estoque)
    db.commit()
    db.refresh(produto)
    return produto
