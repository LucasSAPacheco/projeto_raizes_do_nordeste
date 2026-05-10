from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import (
    PontosFidelidade, HistoricoFidelidade, Pedido, StatusPedido
)

PONTOS_POR_REAL = 1  # 1 ponto a cada R$1,00 gasto


def _get_pontos(db: Session, usuario_id: int) -> PontosFidelidade:
    pontos = db.query(PontosFidelidade).filter(
        PontosFidelidade.usuario_id == usuario_id
    ).first()
    if not pontos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Registro de fidelidade não encontrado para este usuário.")
    return pontos


def consultar_saldo(db: Session, usuario_id: int) -> PontosFidelidade:
    """Retorna o saldo atual de pontos do cliente."""
    return _get_pontos(db, usuario_id)


def ganhar_pontos(db: Session, usuario_id: int, pedido_id: int) -> PontosFidelidade:
    """
    Concede pontos ao cliente com base no valor total do pedido.
    Deve ser chamado após a confirmação do pagamento.
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Pedido não encontrado.")

    if pedido.cliente_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce so pode acumular pontos de pedidos proprios."
        )

    if pedido.status not in (StatusPedido.PAGO, StatusPedido.EM_PREPARO,
                              StatusPedido.PRONTO, StatusPedido.ENTREGUE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pontos só são concedidos após a confirmação do pagamento."
        )

    # Verifica se já ganhou pontos por este pedido
    ja_registrado = db.query(HistoricoFidelidade).filter(
        HistoricoFidelidade.pedido_id == pedido_id,
        HistoricoFidelidade.tipo == "GANHO"
    ).first()
    if ja_registrado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pontos já foram concedidos para este pedido."
        )

    pontos_ganhos = int(pedido.valor_total * PONTOS_POR_REAL)
    if pontos_ganhos <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor do pedido insuficiente para gerar pontos."
        )

    pontos = _get_pontos(db, usuario_id)
    pontos.saldo += pontos_ganhos

    db.add(HistoricoFidelidade(
        pontos_id=pontos.id,
        pedido_id=pedido_id,
        tipo="GANHO",
        quantidade=pontos_ganhos,
    ))

    db.commit()
    db.refresh(pontos)
    return pontos


def resgatar_pontos(db: Session, usuario_id: int, quantidade: int) -> PontosFidelidade:
    """
    Desconta pontos do saldo do cliente para resgate.
    """
    if quantidade <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A quantidade de pontos deve ser maior que zero.")

    pontos = _get_pontos(db, usuario_id)

    if pontos.saldo < quantidade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Saldo insuficiente. Disponível: {pontos.saldo}, solicitado: {quantidade}."
        )

    pontos.saldo -= quantidade

    db.add(HistoricoFidelidade(
        pontos_id=pontos.id,
        tipo="RESGATE",
        quantidade=quantidade,
    ))

    db.commit()
    db.refresh(pontos)
    return pontos


def historico_pontos(db: Session, usuario_id: int) -> list:
    """Retorna o histórico completo de ganhos e resgates do cliente."""
    pontos = _get_pontos(db, usuario_id)
    return db.query(HistoricoFidelidade).filter(
        HistoricoFidelidade.pontos_id == pontos.id
    ).order_by(HistoricoFidelidade.criado_em.desc()).all()
