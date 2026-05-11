import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.application.pedido_service import criar_pedido
from app.application.pagamento_service import solicitar_pagamento
from app.application.fidelidade_service import (
    ganhar_pontos, consultar_saldo
)
from app.domain.models import (
    Usuario, PerfilUsuario, CanalPedido,
    PontosFidelidade, HistoricoFidelidade
)
from app.infrastructure.security import hash_senha


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


@pytest.fixture
def pedido_pago_de_a(db, usuario_cliente, unidade, produto_com_estoque):
    pedido = criar_pedido(
        db=db,
        cliente_id=usuario_cliente.id,
        unidade_id=unidade.id,
        canal_pedido=CanalPedido.APP,
        itens=[{"produto_id": produto_com_estoque.id, "quantidade": 2}],
    )
    with patch("app.application.pagamento_service.random.random", return_value=0.5):
        solicitar_pagamento(db, pedido.id, "PIX")
    db.refresh(pedido)
    return pedido


def test_cliente_nao_pode_ganhar_pontos_de_pedido_alheio(
    db, cliente_b, pedido_pago_de_a, usuario_cliente
):
    saldo_b_antes = consultar_saldo(db, cliente_b.id).saldo
    saldo_a_antes = consultar_saldo(db, usuario_cliente.id).saldo

    with pytest.raises(HTTPException) as exc:
        ganhar_pontos(db, cliente_b.id, pedido_pago_de_a.id)

    assert exc.value.status_code == 403, (
        f"Esperado 403, recebido {exc.value.status_code}: {exc.value.detail}"
    )
    db.expire_all()
    assert consultar_saldo(db, cliente_b.id).saldo == saldo_b_antes
    assert consultar_saldo(db, usuario_cliente.id).saldo == saldo_a_antes

    historico = db.query(HistoricoFidelidade).filter(
        HistoricoFidelidade.pedido_id == pedido_pago_de_a.id
    ).all()
    assert historico == [], "Tentativa bloqueada nao deveria gerar registro de historico."


def test_cliente_pode_ganhar_pontos_do_proprio_pedido(
    db, pedido_pago_de_a, usuario_cliente
):
    pontos = ganhar_pontos(db, usuario_cliente.id, pedido_pago_de_a.id)
    assert pontos.saldo == int(pedido_pago_de_a.valor_total)


def test_apos_bloqueio_dono_ainda_pode_creditar(
    db, cliente_b, pedido_pago_de_a, usuario_cliente
):
    with pytest.raises(HTTPException):
        ganhar_pontos(db, cliente_b.id, pedido_pago_de_a.id)

    pontos = ganhar_pontos(db, usuario_cliente.id, pedido_pago_de_a.id)
    assert pontos.saldo == int(pedido_pago_de_a.valor_total)
