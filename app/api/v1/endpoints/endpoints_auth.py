from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.db.sesion import obtener_sesion
from app.schemas.schemas_auth import RespuestaToken, UsuarioActual
from app.services import servicio_auth

router = APIRouter(prefix="/auth", tags=["Seguridad"])


@router.post("/login", response_model=RespuestaToken, summary="Inicia sesión con usuario y contraseña y devuelve el token")
def login(formulario: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(obtener_sesion)):
    """Los tres roles (administrador del sistema, del negocio y cliente) entran por aquí.
    Se envía como formulario (`username` y `password`), que es lo que usa el botón **Authorize** de Swagger."""
    return servicio_auth.iniciar_sesion(db, formulario.username, formulario.password)


@router.get("/yo", response_model=UsuarioActual, summary="Quién soy: usuario, rol y tienda de la sesión actual")
def yo(usuario: UsuarioActual = Depends(usuario_actual)):
    return usuario
