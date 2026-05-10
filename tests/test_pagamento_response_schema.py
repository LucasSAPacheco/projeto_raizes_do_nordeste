"""
Testes do schema PagamentoResponse.

O modelo Pagamento permite resposta_gateway = NULL no banco, mas o schema
declarava o campo como str obrigatorio. Qualquer pagamento sem resposta
de gateway quebrava a serializacao da resposta da API.
"""
import pytest
from app.api.pagamento_router import PagamentoResponse
from app.domain.models import Pagamento, StatusPagamento


def test_response_aceita_resposta_gateway_nula():
    """
    Bug original: PagamentoResponse exigia resposta_gateway: str.
    Construir a partir de um Pagamento com NULL levantava ValidationError.
    """
    pagamento = Pagamento(
        id=1,
        pedido_id=1,
        forma_pagamento="PIX",
        status=StatusPagamento.APROVADO,
        valor=10.0,
        resposta_gateway=None,
    )

    response = PagamentoResponse.model_validate(pagamento)
    assert response.resposta_gateway is None


def test_response_aceita_resposta_gateway_preenchida():
    """Garante que a serializacao com resposta preenchida segue funcionando."""
    pagamento = Pagamento(
        id=2,
        pedido_id=2,
        forma_pagamento="CARTAO",
        status=StatusPagamento.APROVADO,
        valor=25.5,
        resposta_gateway='{"status": "APROVADO"}',
    )

    response = PagamentoResponse.model_validate(pagamento)
    assert response.resposta_gateway == '{"status": "APROVADO"}'
