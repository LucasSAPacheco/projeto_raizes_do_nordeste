"""
Testes do pagamento mock.
Cobre: pagamento aprovado, pedido inexistente, status inválido,
pagamento duplicado e valor abaixo do mínimo (sempre recusado).
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido
from app.application.pagamento_service import solicitar_pagamento, buscar_pagamento
from app.domain.models import CanalPedido, StatusPedido, StatusPagamento


@pytest.fixture
def pedido(db, usuario_cliente, unidade, produto_com_estoque):
    return criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}]
    )


def test_pagamento_aprovado(db, pedido):
    """Pagamento aprovado deve mudar o status do pedido para PAGO."""
    # Força o gateway a sempre aprovar neste teste
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        pagamento = solicitar_pagamento(db, pedido.id, "PIX")

    assert pagamento.status == StatusPagamento.APROVADO
    assert pagamento.valor == pedido.valor_total
    db.refresh(pedido)
    assert pedido.status == StatusPedido.PAGO


def test_pagamento_recusado_nao_muda_status(db, pedido):
    """Pagamento recusado NÃO deve alterar o status do pedido."""
    with patch("app.application.pagamento_service.random.random", return_value=0.05):
        pagamento = solicitar_pagamento(db, pedido.id, "CARTAO")

    assert pagamento.status == StatusPagamento.RECUSADO
    db.refresh(pedido)
    assert pedido.status == StatusPedido.AGUARDANDO_PAGAMENTO


def test_pagamento_pedido_inexistente(db):
    """Pedido que não existe deve retornar erro 404."""
    with pytest.raises(HTTPException) as exc:
        solicitar_pagamento(db, 9999, "PIX")
    assert exc.value.status_code == 404


def test_pagamento_pedido_status_invalido(db, pedido):
    """Não pode pagar um pedido que não está AGUARDANDO_PAGAMENTO."""
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        solicitar_pagamento(db, pedido.id, "PIX")  # primeiro pagamento aprova

    with pytest.raises(HTTPException) as exc:
        solicitar_pagamento(db, pedido.id, "PIX")  # segundo tenta pagar de novo
    assert exc.value.status_code == 409


def test_pagamento_valor_minimo(db, pedido):
    """Valores abaixo de R$1 são sempre recusados pelo gateway."""
    pedido.valor_total = 0.50
    db.commit()

    pagamento = solicitar_pagamento(db, pedido.id, "PIX")
    assert pagamento.status == StatusPagamento.RECUSADO


def test_buscar_pagamento_inexistente(db):
    """Buscar pagamento de pedido sem pagamento deve retornar 404."""
    with pytest.raises(HTTPException) as exc:
        buscar_pagamento(db, 9999)
    assert exc.value.status_code == 404
