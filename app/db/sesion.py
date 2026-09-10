from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.configuracion import configuracion

motor = create_engine(configuracion.url_base_datos, pool_pre_ping=True)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)


def obtener_sesion():
    sesion = SesionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
