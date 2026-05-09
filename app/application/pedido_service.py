from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import (
    Pedido, ItemPedido, StatusPedido, CanalPedido,
    Produto, Estoque
)


def criar_pedido(db: Session, cliente_id: int, unidade_id: int,
                 canal_pedido: CanalPedido, itens: list[dict],
                 observacao: str = None) -> Pedido:
    """
    Cria um pedido verificando:
    - Se cada produto existe e está disponível
    - Se há estoque suficiente na unidade
    Desconta o estoque e calcula o valor total automaticamente.
    """
    if not itens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O pedido deve ter ao menos um item.")

    pedido = Pedido(
        cliente_id=cliente_id,
        unidade_id=unidade_id,
        canal_pedido=canal_pedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        observacao=observacao,
        valor_total=0.0,
    )
    db.add(pedido)
    db.flush()

    valor_total = 0.0

    for item in itens:
        produto = db.query(Produto).filter(Produto.id == item["produto_id"]).first()

        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Produto {item['produto_id']} não encontrado.")

        if not produto.disponivel:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Produto '{produto.nome}' não está disponível.")

        estoque = db.query(Estoque).filter(
            Estoque.unidade_id == unidade_id,
            Estoque.produto_id == produto.id
        ).first()

        if not estoque or estoque.quantidade < item["quantidade"]:
            disponivel = estoque.quantidade if estoque else 0
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Estoque insuficiente para '{produto.nome}'. "
                       f"Disponível: {disponivel}, solicitado: {item['quantidade']}."
            )

        estoque.quantidade -= item["quantidade"]

        db.add(ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=item["quantidade"],
            preco_unitario=produto.preco,
        ))

        valor_total += produto.preco * item["quantidade"]

    pedido.valor_total = round(valor_total, 2)
    db.commit()
    db.refresh(pedido)
    return pedido
