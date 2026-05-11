from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.infrastructure.security import decodificar_token
from app.domain.models import Usuario, PerfilUsuario

auth_bearer = HTTPBearer()


def get_usuario_atual(
    creds: HTTPAuthorizationCredentials = Depends(auth_bearer),
    db: Session = Depends(get_db)
) -> Usuario:
    payload = decodificar_token(creds.credentials)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo."
        )
    return usuario

def exigir_perfil(*perfis: PerfilUsuario):
    def verificar(usuario: Usuario = Depends(get_usuario_atual)):
        if usuario.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfil necessário: {[p.value for p in perfis]}"
            )
        return usuario
    return verificar
