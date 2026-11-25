"""Dependencias de FastAPI para saber quién llama y qué rol tiene.

Uso en un endpoint:
    usuario: UsuarioActual = Depends(usuario_actual)                       # cualquiera con sesión
    usuario: UsuarioActual = Depends(requiere_rol(RolCodigo.ADMIN_SIS))    # solo ese rol
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.seguridad import leer_token
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import RolCodigo
from app.models.usuarios import Usuario
from app.schemas.schemas_auth import UsuarioActual

# tokenUrl hace que el botón "Authorize" de Swagger (/docs) pida usuario y contraseña y guarde el token.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_NO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sesión no válida o vencida. Inicia sesión de nuevo.",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_actual(token: str = Depends(esquema_oauth2), db: Session = Depends(obtener_sesion)) -> UsuarioActual:
    datos = leer_token(token)
    if datos is None:
        raise _NO_AUTENTICADO
    try:
        id_usuario = int(datos["sub"])
    except (KeyError, ValueError):
        raise _NO_AUTENTICADO

    # Se vuelve a leer de la BD: una baja o un cambio de rol vale de inmediato, aunque el token siga vigente.
    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise _NO_AUTENTICADO
    if not usuario.activo or (usuario.tienda is not None and not usuario.tienda.activo):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La cuenta o la tienda están desactivadas.")
    if usuario.cliente is not None and not usuario.cliente.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La cuenta o la tienda están desactivadas.")

    return UsuarioActual(
        id_usuario=usuario.id_usuario,
        username=usuario.username,
        rol=usuario.rol.codigo,
        tienda_id=usuario.tienda_id,
        id_cliente=usuario.cliente.id_cliente if usuario.cliente is not None else None,
    )


def admin_de_negocio(usuario: UsuarioActual = Depends(usuario_actual)) -> UsuarioActual:
    """Administrador de un negocio, con su tienda asignada. Su `tienda_id` es SIEMPRE la tienda con la que se trabaja:
    nunca se recibe de la petición, así un administrador no puede tocar datos de otra tienda."""
    if usuario.rol != RolCodigo.ADMIN_NEG:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"No tienes permiso para esto. Roles permitidos: {RolCodigo.ADMIN_NEG.value}.")
    if usuario.tienda_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu usuario no tiene una tienda asignada.")
    return usuario


def requiere_rol(*roles: RolCodigo):
    """Deja pasar solo a los roles indicados; a cualquier otro le responde 403."""

    def verificar(usuario: UsuarioActual = Depends(usuario_actual)) -> UsuarioActual:
        if usuario.rol not in roles:
            permitidos = ", ".join(rol.value for rol in roles)
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"No tienes permiso para esto. Roles permitidos: {permitidos}.")
        return usuario

    return verificar
