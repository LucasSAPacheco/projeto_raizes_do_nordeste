import pytest
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido, atualizar_status
from app.domain.models import CanalPedido, StatusPedido


@pytest.fixture
def pedido(db, usuario_cliente, unidade, produto_com_estoque):
    return criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}]
    )


def test_atualizar_status_fluxo_normal(db, pedido):
    p = atualizar_status(db, pedido.id, StatusPedido.PAGO, "ADMIN")
    assert p.status == StatusPedido.PAGO

    p = atualizar_status(db, p.id, StatusPedido.EM_PREPARO, "COZINHA")
    assert p.status == StatusPedido.EM_PREPARO

    p = atualizar_status(db, p.id, StatusPedido.PRONTO, "COZINHA")
    assert p.status == StatusPedido.PRONTO

    p = atualizar_status(db, p.id, StatusPedido.ENTREGUE, "ATENDENTE")
    assert p.status == StatusPedido.ENTREGUE


def test_atualizar_status_transicao_invalida(db, pedido):
    with pytest.raises(HTTPException) as exc:
        atualizar_status(db, pedido.id, StatusPedido.ENTREGUE, "ADMIN")
    assert exc.value.status_code == 409


def test_atualizar_status_pedido_finalizado(db, pedido):
    atualizar_status(db, pedido.id, StatusPedido.PAGO, "ADMIN")
    atualizar_status(db, pedido.id, StatusPedido.EM_PREPARO, "COZINHA")
    atualizar_status(db, pedido.id, StatusPedido.PRONTO, "COZINHA")
    atualizar_status(db, pedido.id, StatusPedido.ENTREGUE, "ATENDENTE")

    with pytest.raises(HTTPException) as exc:
        atualizar_status(db, pedido.id, StatusPedido.CANCELADO, "ADMIN")
    assert exc.value.status_code == 409


def test_cancelar_pedido_pago_sem_permissao(db, pedido):
    atualizar_status(db, pedido.id, StatusPedido.PAGO, "ADMIN")

    with pytest.raises(HTTPException) as exc:
        atualizar_status(db, pedido.id, StatusPedido.CANCELADO, "CLIENTE")
    assert exc.value.status_code == 403


def test_cancelar_pedido_pago_com_permissao(db, pedido):
    atualizar_status(db, pedido.id, StatusPedido.PAGO, "ADMIN")
    p = atualizar_status(db, pedido.id, StatusPedido.CANCELADO, "GERENTE")
    assert p.status == StatusPedido.CANCELADO


def test_atualizar_status_pedido_inexistente(db):
    with pytest.raises(HTTPException) as exc:
        atualizar_status(db, 9999, StatusPedido.PAGO, "ADMIN")
    assert exc.value.status_code == 404
