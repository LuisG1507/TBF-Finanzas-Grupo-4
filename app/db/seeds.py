from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.configuracion import configuracion
from app.core.seguridad import hashear_password
from app.db.sesion import SesionLocal
from app.models.catalogo import Moneda, UnidadMedida
from app.models.enumeraciones import RolCodigo
from app.models.usuarios import Rol, Usuario

ROLES = [
    (RolCodigo.ADMIN_SIS, "Administrador del sistema"),
    (RolCodigo.ADMIN_NEG, "Administrador del negocio"),
    (RolCodigo.CLIENTE, "Cliente"),
]

MONEDAS = [
    ("PEN", "Sol peruano", "S/"),
    ("USD", "Dólar estadounidense", "$"),
]

UNIDADES = [
    ("UND", "Unidad"),
    ("KG", "Kilogramo"),
    ("LT", "Litro"),
]


def _cargar_roles(db: Session) -> int:
    existentes = set(db.scalars(select(Rol.codigo)))
    nuevos = [Rol(codigo=c, nombre=n) for c, n in ROLES if c not in existentes]
    db.add_all(nuevos)
    return len(nuevos)


def _cargar_monedas(db: Session) -> int:
    existentes = set(db.scalars(select(Moneda.codigo_iso)))
    nuevas = [Moneda(codigo_iso=c, nombre=n, simbolo=s) for c, n, s in MONEDAS if c not in existentes]
    db.add_all(nuevas)
    return len(nuevas)


def _cargar_unidades(db: Session) -> int:
    existentes = set(db.scalars(select(UnidadMedida.codigo)))
    nuevas = [UnidadMedida(codigo=c, nombre=n) for c, n in UNIDADES if c not in existentes]
    db.add_all(nuevas)
    return len(nuevas)


def _cargar_admin_sistema(db: Session) -> int:
    """Crea al administrador del sistema con el usuario y la clave de .env. Si ya existe, no lo toca."""
    username, password = configuracion.admin_sistema_usuario, configuracion.admin_sistema_password
    if not username or not password:
        print("AVISO: faltan ADMIN_SISTEMA_USUARIO / ADMIN_SISTEMA_PASSWORD en .env; no se creó el administrador del sistema.")
        return 0
    if db.scalar(select(Usuario).where(Usuario.username == username)) is not None:
        return 0
    rol = db.scalar(select(Rol).where(Rol.codigo == RolCodigo.ADMIN_SIS))
    db.add(Usuario(rol_id=rol.id_rol, tienda_id=None, username=username, password_hash=hashear_password(password)))
    return 1


def cargar_seeds() -> dict[str, int]:
    with SesionLocal() as db:
        resumen = {"roles": _cargar_roles(db)}
        db.flush()  # el administrador necesita que el rol ya exista
        resumen["monedas"] = _cargar_monedas(db)
        resumen["unidades"] = _cargar_unidades(db)
        resumen["administrador_sistema"] = _cargar_admin_sistema(db)
        db.commit()
    return resumen


if __name__ == "__main__":
    for tabla, cantidad in cargar_seeds().items():
        print(f"{tabla}: {cantidad} filas nuevas")
