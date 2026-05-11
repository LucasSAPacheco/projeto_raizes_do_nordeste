import json
import logging
import random
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Pagamento, Pedido, StatusPagamento, StatusPedido

logger = logging.getLogger(__name__)


def _gateway_mock(valor: float, forma_pagamento: str) -> dict:
    if valor < 1.0:
        return {"status": "RECUSADO", "motivo": "Valor abaixo do mínimo permitido."}
    ok = random.random() > 0.10
    if ok:
        return {
            "status": "APROVADO",
            "transaction_id": f"MOCK-{random.randint(100000, 999999)}",
            "forma": forma_pagamento,
            "valor": valor,
        }
    return {"status": "RECUSADO", "motivo": "Pagamento recusado pela operadora."}

def solicitar_pagamento(db: Session, pedido_id: int,
                        forma_pagamento: str) -> Pagamento:
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
    situacao = StatusPagamento.APROVADO \
        if resposta["status"] == "APROVADO" else StatusPagamento.RECUSADO
    pagamento = Pagamento(
        pedido_id=pedido_id,
        forma_pagamento=forma_pagamento,
        status=situacao,
        valor=pedido.valor_total,
        resposta_gateway=json.dumps(resposta),
    )
    db.add(pagamento)
    if situacao == StatusPagamento.APROVADO:
        pedido.status = StatusPedido.PAGO
    db.commit()
    db.refresh(pagamento)
    logger.info(
        "Pagamento pedido_id=%s forma=%s valor=%.2f status=%s",
        pedido_id, forma_pagamento, pagamento.valor, situacao.value
    )
    return pagamento

def buscar_pagamento(db: Session, pedido_id: int) -> Pagamento:
    pagamento = db.query(Pagamento).filter(Pagamento.pedido_id == pedido_id).first()
    if not pagamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Pagamento não encontrado para este pedido.")
    return pagamento
