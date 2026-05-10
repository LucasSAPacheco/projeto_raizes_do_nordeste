"""
Testes de autorizacao em GET /pagamentos/{pedido_id}.

Cliente nao pode consultar o pagamento de um pedido que nao e dele.
Funcionarios mantem acesso pleno.
"""
import pytest
from unittest.mock import patch
from app.application.pedido_service import criar_pedido
from app.application.pagamento_service import solicitar_pagamento
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
    """Segundo cliente para validar isolamento entre contas."""
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


@pytest.fixture
def pedido_pago_de_a(db, usuario_cliente, unidade, produto_com_estoque):
    """Cria um pedido do cliente A e paga com aprovacao garantida."""
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 1}],
    )
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        solicitar_pagamento(db, pedido.id, "PIX")
    return pedido


def test_cliente_nao_pode_ver_pagamento_de_outro_cliente(
    client, cliente_b, pedido_pago_de_a
):
    """
    Bug original: cliente B podia consultar o pagamento de um pedido
    do cliente A apenas adivinhando o ID. Esperado: 403.
    """
    token_b = _login(client, "maria@cliente.com", "senha456")
    resp = client.get(
        f"/pagamentos/{pedido_pago_de_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, (
        f"Cliente B nao deveria ver o pagamento alheio. "
        f"Status: {resp.status_code}, body: {resp.text}"
    )


def test_cliente_pode_ver_proprio_pagamento(client, pedido_pago_de_a):
    """O dono do pedido continua consultando o pagamento normalmente."""
    token = _login(client, "joao@teste.com", "senha123")
    resp = client.get(
        f"/pagamentos/{pedido_pago_de_a.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["pedido_id"] == pedido_pago_de_a.id


def test_funcionario_pode_ver_qualquer_pagamento(
    client, usuario_admin, pedido_pago_de_a
):
    """Funcionarios (ADMIN aqui) seguem com acesso pleno."""
    token = _login(client, "admin@teste.com", "admin123")
    resp = client.get(
        f"/pagamentos/{pedido_pago_de_a.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
