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
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        pagamento = solicitar_pagamento(db, pedido.id, "PIX")

    assert pagamento.status == StatusPagamento.APROVADO
    assert pagamento.valor == pedido.valor_total
    db.refresh(pedido)
    assert pedido.status == StatusPedido.PAGO


def test_pagamento_recusado_nao_muda_status(db, pedido):
    with patch("app.application.pagamento_service.random.random", return_value=0.05):
        pagamento = solicitar_pagamento(db, pedido.id, "CARTAO")

    assert pagamento.status == StatusPagamento.RECUSADO
    db.refresh(pedido)
    assert pedido.status == StatusPedido.AGUARDANDO_PAGAMENTO


def test_pagamento_pedido_inexistente(db):
    with pytest.raises(HTTPException) as exc:
        solicitar_pagamento(db, 9999, "PIX")
    assert exc.value.status_code == 404


def test_pagamento_pedido_status_invalido(db, pedido):
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        solicitar_pagamento(db, pedido.id, "PIX")

    with pytest.raises(HTTPException) as exc:
        solicitar_pagamento(db, pedido.id, "PIX")
    assert exc.value.status_code == 409


def test_pagamento_valor_minimo(db, pedido):
    pedido.valor_total = 0.50
    db.commit()

    pagamento = solicitar_pagamento(db, pedido.id, "PIX")
    assert pagamento.status == StatusPagamento.RECUSADO


def test_buscar_pagamento_inexistente(db):
    with pytest.raises(HTTPException) as exc:
        buscar_pagamento(db, 9999)
    assert exc.value.status_code == 404
