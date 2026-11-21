"""Seguridad: contraseñas (bcrypt) y tokens de sesión (JWT).

- Contraseñas: nunca se guardan; se guarda el hash bcrypt (con sal propia). bcrypt solo mira los
  primeros 72 bytes, por eso se rechazan contraseñas más largas en lugar de truncarlas en silencio.
- Token: JWT firmado con HS256 y la `clave_secreta` de la configuración. Lleva solo lo necesario
  (id de usuario, rol, tienda) y vence a los `minutos_expiracion_token`.
  El token NO es la fuente de verdad: en cada petición se vuelve a leer al usuario de la BD
  (ver app/api/dependencias.py), así una baja o un cambio de rol surte efecto de inmediato.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.configuracion import configuracion

ALGORITMO_JWT = "HS256"
MAX_BYTES_PASSWORD = 72


def _a_bytes(password: str) -> bytes:
    datos = password.encode("utf-8")
    if len(datos) > MAX_BYTES_PASSWORD:
        raise ValueError(f"La contraseña no puede pasar de {MAX_BYTES_PASSWORD} bytes")
    return datos


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(_a_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_a_bytes(password), password_hash.encode("utf-8"))
    except ValueError:  # contraseña demasiado larga o hash con formato inválido
        return False


# Hash de una contraseña inventada: sirve para gastar el mismo tiempo cuando el usuario no existe
# y así no revelar, por la demora de la respuesta, qué usuarios están registrados.
HASH_SEÑUELO = hashear_password("contraseña-señuelo-no-valida")


def crear_token(id_usuario: int, rol: str, tienda_id: int | None, vence_en: timedelta | None = None) -> str:
    ahora = datetime.now(timezone.utc)
    duracion = vence_en if vence_en is not None else timedelta(minutes=configuracion.minutos_expiracion_token)
    datos = {
        "sub": str(id_usuario),
        "rol": rol,
        "tienda_id": tienda_id,
        "iat": ahora,
        "exp": ahora + duracion,
    }
    return jwt.encode(datos, configuracion.clave_secreta, algorithm=ALGORITMO_JWT)


def leer_token(token: str) -> dict | None:
    """Devuelve el contenido del token, o None si está mal firmado, alterado o vencido."""
    try:
        return jwt.decode(token, configuracion.clave_secreta, algorithms=[ALGORITMO_JWT])
    except JWTError:
        return None
