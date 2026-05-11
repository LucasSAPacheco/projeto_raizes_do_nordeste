from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import StatusPagamento, Usuario, PerfilUsuario
from app.api.deps import get_usuario_atual
from app.application.pagamento_service import solicitar_pagamento, buscar_pagamento

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

class PagamentoRequest(BaseModel):
    pedido_id: int
    forma_pagamento: str

class PagamentoResponse(BaseModel):
    id: int
    pedido_id: int
    forma_pagamento: str
    status: StatusPagamento
    valor: float
    resposta_gateway: Optional[str] = None
    class Config:
        from_attributes = True

@router.post("", response_model=PagamentoResponse, status_code=201,
             summary="Solicitar pagamento")
def pagar(body: PagamentoRequest,
          usuario_atual: Usuario = Depends(get_usuario_atual),
          db: Session = Depends(get_db)):
    return solicitar_pagamento(db, body.pedido_id, body.forma_pagamento)


@router.get("/{pedido_id}", response_model=PagamentoResponse,
            summary="Consultar pagamento do pedido")
def consultar(pedido_id: int,
              usuario_atual: Usuario = Depends(get_usuario_atual),
              db: Session = Depends(get_db)):
    pagamento = buscar_pagamento(db, pedido_id)
    if (usuario_atual.perfil == PerfilUsuario.CLIENTE
            and pagamento.pedido.cliente_id != usuario_atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para acessar este pagamento.",
        )
    return pagamento
