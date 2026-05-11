import pytest
from app.application.pedido_service import criar_pedido
from app.domain.models import (
    Usuario, PerfilUsuario, CanalPedido, PontosFidelidade
)
from app.infrastructure.security import hash_senha


def _login(client, email, senha):
    resp = client.post("/auth/login", json={"email": email, "senha": senha})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def cliente_b(db):
    usuario = Usuario(
        nome="Maria Outra",
        email="maria@cliente.com",
        senha_hash=hash_senha("senha456"),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True,
    )
    db.add(usuario)
    db.flush()
    db.add(PontosFidelidade(usuario_id=usuario.id, saldo=0))
    db.commit()
    db.refresh(usuario)
    return usuario


def test_cliente_nao_pode_ver_pedido_de_outro_cliente(
    client, db, usuario_cliente, cliente_b, unidade, produto_com_estoque
):
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}],
    )

    token_b = _login(client, "maria@cliente.com", "senha456")
    resp = client.get(
        f"/pedidos/{pedido.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, (
        f"Cliente B nao deveria acessar pedido do cliente A. "
        f"Status retornado: {resp.status_code}, body: {resp.text}"
    )


def test_cliente_pode_ver_proprio_pedido(
    client, db, usuario_cliente, unidade, produto_com_estoque
):
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}],
    )

    token_a = _login(client, "joao@teste.com", "senha123")
    resp = client.get(
        f"/pedidos/{pedido.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == pedido.id


def test_funcionario_pode_ver_qualquer_pedido(
    client, db, usuario_cliente, usuario_admin, unidade, produto_com_estoque
):
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}],
    )

    token_admin = _login(client, "admin@teste.com", "admin123")
    resp = client.get(
        f"/pedidos/{pedido.id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
