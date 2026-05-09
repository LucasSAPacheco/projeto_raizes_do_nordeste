from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import PerfilUsuario
from app.api.deps import exigir_perfil
from app.application.unidade_service import (
    listar_unidades, buscar_unidade, criar_unidade,
    atualizar_unidade, desativar_unidade
)

router = APIRouter(prefix="/unidades", tags=["Unidades"])


# ── Schemas ─────────────────────────────────────────────

class UnidadeRequest(BaseModel):
    nome: str
    endereco: str
    cidade: str
    estado: str


class UnidadeUpdateRequest(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    ativa: Optional[bool] = None


class UnidadeResponse(BaseModel):
    id: int
    nome: str
    endereco: str
    cidade: str
    estado: str
    ativa: bool

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────

@router.get("", response_model=list[UnidadeResponse], summary="Listar unidades")
def listar(apenas_ativas: bool = True, db: Session = Depends(get_db)):
    """Lista todas as unidades da rede. Por padrão retorna apenas as ativas."""
    return listar_unidades(db, apenas_ativas)


@router.get("/{unidade_id}", response_model=UnidadeResponse, summary="Buscar unidade")
def buscar(unidade_id: int, db: Session = Depends(get_db)):
    """Retorna os dados de uma unidade pelo ID."""
    return buscar_unidade(db, unidade_id)


@router.post("", response_model=UnidadeResponse, status_code=201,
             summary="Criar unidade",
             dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))])
def criar(body: UnidadeRequest, db: Session = Depends(get_db)):
    """Cadastra uma nova unidade da rede. Apenas ADMIN ou GERENTE podem criar."""
    return criar_unidade(db, body.nome, body.endereco, body.cidade, body.estado)


@router.patch("/{unidade_id}", response_model=UnidadeResponse, summary="Atualizar unidade",
              dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))])
def atualizar(unidade_id: int, body: UnidadeUpdateRequest, db: Session = Depends(get_db)):
    """Atualiza os dados de uma unidade. Apenas ADMIN ou GERENTE."""
    return atualizar_unidade(db, unidade_id, body.model_dump(exclude_none=True))


@router.delete("/{unidade_id}", response_model=UnidadeResponse, summary="Desativar unidade",
               dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN))])
def desativar(unidade_id: int, db: Session = Depends(get_db)):
    """Desativa uma unidade (não apaga do banco). Apenas ADMIN."""
    return desativar_unidade(db, unidade_id)
