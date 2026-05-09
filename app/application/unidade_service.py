from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Unidade


def listar_unidades(db: Session, apenas_ativas: bool = True):
    query = db.query(Unidade)
    if apenas_ativas:
        query = query.filter(Unidade.ativa == True)
    return query.all()


def buscar_unidade(db: Session, unidade_id: int) -> Unidade:
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Unidade não encontrada.")
    return unidade


def criar_unidade(db: Session, nome: str, endereco: str,
                  cidade: str, estado: str) -> Unidade:
    unidade = Unidade(nome=nome, endereco=endereco, cidade=cidade, estado=estado)
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


def atualizar_unidade(db: Session, unidade_id: int, dados: dict) -> Unidade:
    unidade = buscar_unidade(db, unidade_id)
    for campo, valor in dados.items():
        if valor is not None:
            setattr(unidade, campo, valor)
    db.commit()
    db.refresh(unidade)
    return unidade


def desativar_unidade(db: Session, unidade_id: int) -> Unidade:
    unidade = buscar_unidade(db, unidade_id)
    unidade.ativa = False
    db.commit()
    db.refresh(unidade)
    return unidade
