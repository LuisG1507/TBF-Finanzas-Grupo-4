from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio, requiere_rol
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import EstadoCuentaEstado, RolCodigo
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_estados_cuenta import EstadoCuentaRespuesta, EstadoCuentaResumen, GenerarEstadosCuenta
from app.services import servicio_estados_cuenta

router = APIRouter(tags=["Estados de cuenta"])

AdminNegocio = Annotated[UsuarioActual, Depends(admin_de_negocio)]
ClienteActual = Annotated[UsuarioActual, Depends(requiere_rol(RolCodigo.CLIENTE))]
Sesion = Annotated[Session, Depends(obtener_sesion)]
Anio = Annotated[int | None, Query(ge=1, le=9999)]
Mes = Annotated[int | None, Query(ge=1, le=12)]
Limite = Annotated[int, Query(ge=1, le=200)]
Desplazamiento = Annotated[int, Query(ge=0)]


@router.post("/estados-cuenta/generar", response_model=list[EstadoCuentaResumen], summary="Emite los cortes del mes que ya se cumplieron")
def generar(datos: GenerarEstadosCuenta, usuario: AdminNegocio, db: Sesion):
    return servicio_estados_cuenta.generar(db, usuario.tienda_id, usuario.id_usuario, datos.anio, datos.mes)


@router.get("/estados-cuenta", response_model=list[EstadoCuentaResumen], summary="Estados de cuenta de tu tienda")
def listar(
    usuario: AdminNegocio,
    db: Sesion,
    cliente_id: Annotated[int | None, Query(gt=0)] = None,
    anio: Anio = None,
    mes: Mes = None,
    estado: EstadoCuentaEstado | None = None,
    limite: Limite = 50,
    desplazamiento: Desplazamiento = 0,
):
    return servicio_estados_cuenta.listar(db, usuario.tienda_id, cliente_id, anio, mes, estado, limite, desplazamiento)


@router.get("/estados-cuenta/{id_estado_cuenta}", response_model=EstadoCuentaRespuesta, summary="Detalle de un estado de cuenta de tu tienda")
def obtener(id_estado_cuenta: int, usuario: AdminNegocio, db: Sesion):
    return servicio_estados_cuenta.obtener(db, usuario.tienda_id, id_estado_cuenta)


def _identidad_cliente(usuario: UsuarioActual) -> tuple[int, int]:
    if usuario.tienda_id is None or usuario.id_cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu usuario no está asociado a ningún cliente.")
    return usuario.tienda_id, usuario.id_cliente


@router.get("/mi-cuenta/estados-cuenta", response_model=list[EstadoCuentaResumen], summary="Tus estados de cuenta")
def listar_propios(
    usuario: ClienteActual,
    db: Sesion,
    anio: Anio = None,
    mes: Mes = None,
    estado: EstadoCuentaEstado | None = None,
    limite: Limite = 50,
    desplazamiento: Desplazamiento = 0,
):
    tienda_id, cliente_id = _identidad_cliente(usuario)
    return servicio_estados_cuenta.listar(db, tienda_id, cliente_id, anio, mes, estado, limite, desplazamiento)


@router.get("/mi-cuenta/estados-cuenta/{id_estado_cuenta}", response_model=EstadoCuentaRespuesta, summary="Detalle de tu estado de cuenta")
def obtener_propio(id_estado_cuenta: int, usuario: ClienteActual, db: Sesion):
    tienda_id, cliente_id = _identidad_cliente(usuario)
    return servicio_estados_cuenta.obtener(db, tienda_id, id_estado_cuenta, cliente_id)
