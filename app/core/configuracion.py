from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    nombre_app: str = "TBF Finanzas API"
    url_base_datos: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/tbf_finanzas"
    clave_secreta: str = "2312"
    minutos_expiracion_token: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


configuracion = Configuracion()
