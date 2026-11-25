from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencias import requiere_rol
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import RolCodigo
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_tiendas import TiendaActualizar, TiendaCrear, TiendaCreadaRespuesta, TiendaRespuesta
from app.services import servicio_tiendas

router = APIRouter(tags=["Tiendas"])

solo_admin_sistema = requiere_rol(RolCodigo.ADMIN_SIS)


@router.post(
    "/tiendas",
    response_model=TiendaCreadaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de una tienda con las credenciales de su administrador (administrador del sistema)",
)
def crear_tienda(datos: TiendaCrear, actor: UsuarioActual = Depends(solo_admin_sistema), db: Session = Depends(obtener_sesion)):
    return servicio_tiendas.crear(db, datos, actor)


@router.get("/tiendas", response_model=list[TiendaRespuesta], summary="Lista las tiendas (administrador del sistema)")
def listar_tiendas(
    activo: bool | None = Query(default=None, description="true = solo activas, false = solo dadas de baja"),
    buscar: str | None = Query(default=None, description="Texto a buscar en razón social, nombre comercial, RUC o giro"),
    limite: int = Query(default=50, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
    _: UsuarioActual = Depends(solo_admin_sistema),
    db: Session = Depends(obtener_sesion),
):
    return servicio_tiendas.listar(db, activo, buscar, limite, desplazamiento)


@router.get(
    "/mi-tienda",
    response_model=TiendaRespuesta,
    summary="Los datos de la tienda de quien inició sesión (administrador del negocio o cliente)",
)
def mi_tienda(
    usuario: UsuarioActual = Depends(requiere_rol(RolCodigo.ADMIN_NEG, RolCodigo.CLIENTE)),
    db: Session = Depends(obtener_sesion),
):
    if usuario.tienda_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu usuario no está asociado a ninguna tienda.")
    return servicio_tiendas.obtener(db, usuario.tienda_id)


@router.get("/tiendas/{id_tienda}", response_model=TiendaRespuesta, summary="Una tienda (administrador del sistema)")
def ver_tienda(id_tienda: int, _: UsuarioActual = Depends(solo_admin_sistema), db: Session = Depends(obtener_sesion)):
    return servicio_tiendas.obtener(db, id_tienda)


@router.patch("/tiendas/{id_tienda}", response_model=TiendaRespuesta, summary="Modifica datos de una tienda; solo cambia lo que se envía")
def modificar_tienda(
    id_tienda: int,
    datos: TiendaActualizar,
    actor: UsuarioActual = Depends(solo_admin_sistema),
    db: Session = Depends(obtener_sesion),
):
    return servicio_tiendas.actualizar(db, id_tienda, datos, actor)


@router.post("/tiendas/{id_tienda}/baja", response_model=TiendaRespuesta, summary="Da de baja una tienda: nadie de esa tienda podrá entrar")
def dar_de_baja_tienda(id_tienda: int, actor: UsuarioActual = Depends(solo_admin_sistema), db: Session = Depends(obtener_sesion)):
    return servicio_tiendas.dar_de_baja(db, id_tienda, actor)


@router.post("/tiendas/{id_tienda}/alta", response_model=TiendaRespuesta, summary="Reactiva una tienda dada de baja")
def reactivar_tienda(id_tienda: int, actor: UsuarioActual = Depends(solo_admin_sistema), db: Session = Depends(obtener_sesion)):
    return servicio_tiendas.reactivar(db, id_tienda, actor)
