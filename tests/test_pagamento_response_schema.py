import pytest
from app.api.pagamento_router import PagamentoResponse
from app.domain.models import Pagamento, StatusPagamento


def test_response_aceita_resposta_gateway_nula():
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
