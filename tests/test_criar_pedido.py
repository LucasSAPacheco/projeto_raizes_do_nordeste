"""
Testes da função criar_pedido.
Cobre: criação com sucesso, pedido sem itens, produto inexistente,
produto indisponível e estoque insuficiente.
"""
import pytest
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido
from app.domain.models import CanalPedido, StatusPedido


def test_criar_pedido_sucesso(db, usuario_cliente, unidade, produto_com_estoque):
    """Cria um pedido normal e verifica valor total e desconto do estoque."""
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 2}]
    )

    assert pedido.id is not None
    assert pedido.status == StatusPedido.AGUARDANDO_PAGAMENTO
    assert pedido.canal_pedido == CanalPedido.APP
    assert pedido.valor_total == round(produto_com_estoque.preco * 2, 2)
    assert len(pedido.itens) == 1
    # Verifica que o estoque foi descontado (era 10, saiu 2)
    from app.domain.models import Estoque
    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == unidade.id,
        Estoque.produto_id == produto_com_estoque.id
    ).first()
    assert estoque.quantidade == 8


def test_criar_pedido_sem_itens(db, usuario_cliente, unidade):
    """Pedido vazio deve retornar erro 400."""
    with pytest.raises(HTTPException) as exc:
        criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.TOTEM, itens=[])
    assert exc.value.status_code == 400


def test_criar_pedido_produto_inexistente(db, usuario_cliente, unidade):
    """Produto que não existe deve retornar erro 404."""
    with pytest.raises(HTTPException) as exc:
        criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.WEB,
                     itens=[{"produto_id": 9999, "quantidade": 1}])
    assert exc.value.status_code == 404


def test_criar_pedido_produto_indisponivel(db, usuario_cliente, unidade, produto_com_estoque):
    """Produto marcado como indisponível deve retornar erro 409."""
    produto_com_estoque.disponivel = False
    db.commit()

    with pytest.raises(HTTPException) as exc:
        criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.BALCAO,
                     itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}])
    assert exc.value.status_code == 409


def test_criar_pedido_estoque_insuficiente(db, usuario_cliente, unidade, produto_com_estoque):
    """Pedir mais do que tem no estoque deve retornar erro 409."""
    with pytest.raises(HTTPException) as exc:
        criar_pedido(db, usuario_cliente.id, unidade.id, CanalPedido.APP,
                     itens=[{"produto_id": produto_com_estoque.id, "quantidade": 999}])
    assert exc.value.status_code == 409
