from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Produto


def listar_produtos(db: Session, categoria: str = None, apenas_disponiveis: bool = True):
    query = db.query(Produto)
    if apenas_disponiveis:
        query = query.filter(Produto.disponivel == True)
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    return query.all()


def buscar_produto(db: Session, produto_id: int) -> Produto:
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Produto não encontrado.")
    return produto


def criar_produto(db: Session, nome: str, descricao: str,
                  preco: float, categoria: str) -> Produto:
    produto = Produto(nome=nome, descricao=descricao, preco=preco, categoria=categoria)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar_produto(db: Session, produto_id: int, dados: dict) -> Produto:
    produto = buscar_produto(db, produto_id)
    for campo, valor in dados.items():
        if valor is not None:
            setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto


def remover_produto(db: Session, produto_id: int) -> Produto:
    produto = buscar_produto(db, produto_id)
    produto.disponivel = False
    db.commit()
    db.refresh(produto)
    return produto
