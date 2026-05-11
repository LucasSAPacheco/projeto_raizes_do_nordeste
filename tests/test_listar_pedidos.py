import pytest
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido, listar_pedidos, buscar_pedido
from app.domain.models import CanalPedido, StatusPedido


@pytest.fixture
def tres_pedidos(db, usuario_cliente, unidade, produto_com_estoque):
    p1 = criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.APP,
                      [{"produto_id": produto_com_estoque.id, "quantidade": 1}])
    p2 = criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.TOTEM,
                      [{"produto_id": produto_com_estoque.id, "quantidade": 1}])
    p3 = criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.WEB,
                      [{"produto_id": produto_com_estoque.id, "quantidade": 1}])
    return [p1, p2, p3]


def test_listar_todos_os_pedidos(db, tres_pedidos):
    resultado = listar_pedidos(db)
    assert len(resultado) == 3


def test_filtrar_por_canal(db, tres_pedidos):
    resultado = listar_pedidos(db, canal_pedido=CanalPedido.APP)
    assert len(resultado) == 1
    assert resultado[0].canal_pedido == CanalPedido.APP


def test_filtrar_por_status(db, tres_pedidos):
    resultado = listar_pedidos(db, status_pedido=StatusPedido.AGUARDANDO_PAGAMENTO)
    assert len(resultado) == 3

    resultado_pago = listar_pedidos(db, status_pedido=StatusPedido.PAGO)
    assert len(resultado_pago) == 0


def test_filtrar_por_unidade(db, tres_pedidos, unidade):
    resultado = listar_pedidos(db, unidade_id=unidade.id)
    assert len(resultado) == 3


def test_paginacao(db, tres_pedidos):
    pagina1 = listar_pedidos(db, page=1, limit=2)
    pagina2 = listar_pedidos(db, page=2, limit=2)
    assert len(pagina1) == 2
    assert len(pagina2) == 1


def test_buscar_pedido_inexistente(db):
    with pytest.raises(HTTPException) as exc:
        buscar_pedido(db, 9999)
    assert exc.value.status_code == 404
