from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Estoque, MovimentacaoEstoque, TipoMovimentacaoEstoque


def buscar_estoque(db: Session, unidade_id: int, produto_id: int) -> Estoque:
    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == unidade_id,
        Estoque.produto_id == produto_id
    ).first()
    if not estoque:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Estoque não encontrado para esse produto nessa unidade.")
    return estoque


def listar_estoque_por_unidade(db: Session, unidade_id: int):
    return db.query(Estoque).filter(Estoque.unidade_id == unidade_id).all()


def movimentar_estoque(db: Session, unidade_id: int, produto_id: int,
                       tipo: TipoMovimentacaoEstoque, quantidade: int,
                       observacao: str = None) -> Estoque:
    if quantidade <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A quantidade deve ser maior que zero.")

    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == unidade_id,
        Estoque.produto_id == produto_id
    ).first()

    # Cria o registro de estoque se ainda não existir
    if not estoque:
        if tipo == TipoMovimentacaoEstoque.SAIDA:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Não há estoque cadastrado para esse produto nessa unidade.")
        estoque = Estoque(unidade_id=unidade_id, produto_id=produto_id, quantidade=0)
        db.add(estoque)
        db.flush()

    if tipo == TipoMovimentacaoEstoque.SAIDA:
        if estoque.quantidade < quantidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Estoque insuficiente. Disponível: {estoque.quantidade}, solicitado: {quantidade}."
            )
        estoque.quantidade -= quantidade
    else:
        estoque.quantidade += quantidade

    db.add(MovimentacaoEstoque(
        estoque_id=estoque.id,
        tipo=tipo,
        quantidade=quantidade,
        observacao=observacao
    ))

    db.commit()
    db.refresh(estoque)
    return estoque
