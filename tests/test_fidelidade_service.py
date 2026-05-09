"""
Testes do serviço de fidelidade.
Cobre: ganhar pontos, pontos duplicados, pedido não pago,
resgatar pontos, saldo insuficiente e histórico.
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido
from app.application.pagamento_service import solicitar_pagamento
from app.application.fidelidade_service import (
    ganhar_pontos, resgatar_pontos, consultar_saldo, historico_pontos
)
from app.domain.models import CanalPedido


@pytest.fixture
def pedido_pago(db, usuario_cliente, unidade, produto_com_estoque):
    """Cria e paga um pedido para usar nos testes de fidelidade."""
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 2}]
    )
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        solicitar_pagamento(db, pedido.id, "PIX")
    db.refresh(pedido)
    return pedido


def test_ganhar_pontos_sucesso(db, usuario_cliente, pedido_pago):
    """Deve creditar pontos equivalentes ao valor do pedido."""
    pontos = ganhar_pontos(db, usuario_cliente.id, pedido_pago.id)
    esperado = int(pedido_pago.valor_total)
    assert pontos.saldo == esperado


def test_ganhar_pontos_duplicado(db, usuario_cliente, pedido_pago):
    """Não deve conceder pontos duas vezes pelo mesmo pedido."""
    ganhar_pontos(db, usuario_cliente.id, pedido_pago.id)

    with pytest.raises(HTTPException) as exc:
        ganhar_pontos(db, usuario_cliente.id, pedido_pago.id)
    assert exc.value.status_code == 409


def test_ganhar_pontos_pedido_nao_pago(db, usuario_cliente, unidade, produto_com_estoque):
    """Não deve conceder pontos para pedido ainda não pago."""
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.WEB,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}]
    )
    with pytest.raises(HTTPException) as exc:
        ganhar_pontos(db, usuario_cliente.id, pedido.id)
    assert exc.value.status_code == 409


def test_resgatar_pontos_sucesso(db, usuario_cliente, pedido_pago):
    """Deve descontar os pontos resgatados do saldo."""
    ganhar_pontos(db, usuario_cliente.id, pedido_pago.id)
    saldo_antes = consultar_saldo(db, usuario_cliente.id).saldo

    pontos = resgatar_pontos(db, usuario_cliente.id, 5)
    assert pontos.saldo == saldo_antes - 5


def test_resgatar_pontos_saldo_insuficiente(db, usuario_cliente):
    """Resgatar mais do que tem deve retornar erro 409."""
    with pytest.raises(HTTPException) as exc:
        resgatar_pontos(db, usuario_cliente.id, 9999)
    assert exc.value.status_code == 409


def test_historico_registra_ganho_e_resgate(db, usuario_cliente, pedido_pago):
    """O histórico deve registrar tanto ganhos quanto resgates."""
    ganhar_pontos(db, usuario_cliente.id, pedido_pago.id)
    resgatar_pontos(db, usuario_cliente.id, 5)

    hist = historico_pontos(db, usuario_cliente.id)
    tipos = [h.tipo for h in hist]
    assert "GANHO" in tipos
    assert "RESGATE" in tipos
