"""Inicio de sesión: comprueba usuario y contraseña y arma el token."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.configuracion import configuracion
from app.core.seguridad import HASH_SEÑUELO, crear_token, verificar_password
from app.models.usuarios import Usuario
from app.schemas.schemas_auth import RespuestaToken

_CREDENCIALES_MALAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Usuario o contraseña incorrectos.",
    headers={"WWW-Authenticate": "Bearer"},
)


def iniciar_sesion(db: Session, username: str, password: str) -> RespuestaToken:
    usuario = db.scalar(select(Usuario).where(Usuario.username == username))

    # Siempre se hace una verificación de bcrypt, exista o no el usuario, para que la demora no delate cuáles existen.
    hash_a_probar = usuario.password_hash if usuario is not None else HASH_SEÑUELO
    password_ok = verificar_password(password, hash_a_probar)
    if usuario is None or not password_ok:
        raise _CREDENCIALES_MALAS

    # Recién con la contraseña correcta se dice si la cuenta está dada de baja.
    cuenta_activa = usuario.activo and (usuario.tienda is None or usuario.tienda.activo)
    if usuario.cliente is not None and not usuario.cliente.activo:
        cuenta_activa = False
    if not cuenta_activa:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La cuenta o la tienda están desactivadas.")

    token = crear_token(usuario.id_usuario, usuario.rol.codigo.value, usuario.tienda_id)
    return RespuestaToken(
        access_token=token,
        expira_en_minutos=configuracion.minutos_expiracion_token,
        rol=usuario.rol.codigo,
    )
