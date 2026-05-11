import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.domain.models import Usuario, PerfilUsuario, PontosFidelidade
from app.infrastructure.security import hash_senha, verificar_senha, criar_token

logger = logging.getLogger(__name__)

def cadastrar_usuario(db: Session, nome: str, email: str, senha: str,
                      perfil: PerfilUsuario, consentimento_lgpd: bool) -> Usuario:
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com esse e-mail."
        )
    if not consentimento_lgpd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário aceitar os termos de uso e política de privacidade (LGPD)."
        )
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_senha(senha),
        perfil=perfil,
        consentimento_lgpd=consentimento_lgpd,
    )
    db.add(usuario)
    db.flush()
    if perfil == PerfilUsuario.CLIENTE:
        db.add(PontosFidelidade(usuario_id=usuario.id, saldo=0))
    db.commit()
    db.refresh(usuario)
    return usuario


def login(db: Session, email: str, senha: str) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        logger.warning("Falha de login para email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.ativo:
        logger.warning("Tentativa de login de usuario inativo id=%s", usuario.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Entre em contato com o suporte."
        )
    token = criar_token({"sub": str(usuario.id), "perfil": usuario.perfil.value})
    logger.info("Login OK usuario_id=%s perfil=%s", usuario.id, usuario.perfil.value)
    return {"access_token": token, "token_type": "bearer"}
