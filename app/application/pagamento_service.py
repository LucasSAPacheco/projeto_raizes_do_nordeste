import json
import random
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Pagamento, Pedido, StatusPagamento, StatusPedido


def _gateway_mock(valor: float, forma_pagamento: str) -> dict:
    """
    Simula a chamada a um serviço externo de pagamento.
    Em produção real, aqui entraria o SDK do Mercado Pago, PicPay, etc.
    Retorna aprovado para a maioria dos casos, recusado para valores < R$1.
    """
    if valor < 1.0:
        return {"status": "RECUSADO", "motivo": "Valor abaixo do mínimo permitido."}

    # Simula uma taxa de aprovação de 90%
    aprovado = random.random() > 0.10
    if aprovado:
        return {
            "status": "APROVADO",
            "transaction_id": f"MOCK-{random.randint(100000, 999999)}",
            "forma": forma_pagamento,
            "valor": valor,
        }
    return {"status": "RECUSADO", "motivo": "Pagamento recusado pela operadora."}


def solicitar_pagamento(db: Session, pedido_id: int,
                        forma_pagamento: str) -> Pagamento:
    """
    Envia o pedido para o gateway mock e registra o resultado.
    Se aprovado, atualiza o status do pedido para PAGO automaticamente.
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Pedido não encontrado.")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pedido não está aguardando pagamento. Status atual: {pedido.status.value}."
        )

    if db.query(Pagamento).filter(Pagamento.pedido_id == pedido_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um pagamento registrado para este pedido."
        )

    resposta = _gateway_mock(pedido.valor_total, forma_pagamento)
    status_pagamento = StatusPagamento.APROVADO \
        if resposta["status"] == "APROVADO" else StatusPagamento.RECUSADO

    pagamento = Pagamento(
        pedido_id=pedido_id,
        forma_pagamento=forma_pagamento,
        status=status_pagamento,
        valor=pedido.valor_total,
        resposta_gateway=json.dumps(resposta),
    )
    db.add(pagamento)

    if status_pagamento == StatusPagamento.APROVADO:
        pedido.status = StatusPedido.PAGO

    db.commit()
    db.refresh(pagamento)
    return pagamento


def buscar_pagamento(db: Session, pedido_id: int) -> Pagamento:
    """Retorna o pagamento de um pedido ou 404."""
    pagamento = db.query(Pagamento).filter(Pagamento.pedido_id == pedido_id).first()
    if not pagamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Pagamento não encontrado para este pedido.")
    return pagamento
