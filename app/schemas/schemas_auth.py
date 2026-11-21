from pydantic import BaseModel

from app.models.enumeraciones import RolCodigo


class RespuestaToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_minutos: int
    rol: RolCodigo


class UsuarioActual(BaseModel):
    """Quién está conectado, tal como lo ve la API."""

    id_usuario: int
    username: str
    rol: RolCodigo
    tienda_id: int | None  # None para el administrador del sistema
    id_cliente: int | None  # solo si el usuario es un cliente
