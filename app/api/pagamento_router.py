from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import StatusPagamento, Usuario, PerfilUsuario
from app.api.deps import get_usuario_atual
from app.application.pagamento_service import solicitar_pagamento, buscar_pagamento

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


# ── Schemas ─────────────────────────────────────────────

class PagamentoRequest(BaseModel):
    pedido_id: int
    forma_pagamento: str


class PagamentoResponse(BaseModel):
    id: int
    pedido_id: int
    forma_pagamento: str
    status: StatusPagamento
    valor: float
    resposta_gateway: str

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────

@router.post("", response_model=PagamentoResponse, status_code=201,
             summary="Solicitar pagamento")
def pagar(body: PagamentoRequest,
          usuario_atual: Usuario = Depends(get_usuario_atual),
          db: Session = Depends(get_db)):
    """
    Envia o pedido para o gateway de pagamento (simulado).
    Se aprovado, o status do pedido é atualizado para PAGO automaticamente.
    Formas de pagamento aceitas: PIX, CARTAO, DINHEIRO, VALE_REFEICAO.
    """
    return solicitar_pagamento(db, body.pedido_id, body.forma_pagamento)


@router.get("/{pedido_id}", response_model=PagamentoResponse,
            summary="Consultar pagamento do pedido")
def consultar(pedido_id: int,
              usuario_atual: Usuario = Depends(get_usuario_atual),
              db: Session = Depends(get_db)):
    """
    Retorna o registro de pagamento de um pedido.
    Cliente so pode consultar pagamentos dos proprios pedidos;
    funcionarios consultam qualquer um.
    """
    pagamento = buscar_pagamento(db, pedido_id)
    if (usuario_atual.perfil == PerfilUsuario.CLIENTE
            and pagamento.pedido.cliente_id != usuario_atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para acessar este pagamento.",
        )
    return pagamento
