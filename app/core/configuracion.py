from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    nombre_app: str = "Bizon API"
    url_base_datos: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/tbf_finanzas"
    clave_secreta: str = "2312"
    minutos_expiracion_token: int = 60
    # Soles por 1 dólar. Fijo por decisión del equipo; se cambia aquí o en .env (TIPO_CAMBIO_USD_PEN).
    tipo_cambio_usd_pen: Decimal = Decimal("3.47")
    # Administrador del sistema inicial: los seeds lo crean con estos datos. Van en .env (que no se sube a git).
    admin_sistema_usuario: str | None = None
    admin_sistema_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


configuracion = Configuracion()
