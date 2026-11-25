from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio, requiere_rol
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import RolCodigo
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_compras import CompraRespuesta
from app.schemas.schemas_resumen import RespuestaTablero, ResumenMiCuenta
from app.services import servicio_compras, servicio_resumen

router = APIRouter(tags=["Tablero y mi cuenta"])
Sesion = Annotated[Session, Depends(obtener_sesion)]
AdminNegocio = Annotated[UsuarioActual, Depends(admin_de_negocio)]


def identidad_cliente(usuario: Annotated[UsuarioActual, Depends(requiere_rol(RolCodigo.CLIENTE))]) -> tuple[int, int]:
    if usuario.tienda_id is None or usuario.id_cliente is None:
        raise HTTPException(404, "Tu usuario no está asociado a ningún cliente.")
    return usuario.tienda_id, usuario.id_cliente


ClienteActual = Annotated[tuple[int, int], Depends(identidad_cliente)]


@router.get("/dashboard", response_model=RespuestaTablero, summary="Cartera y cobranza de tu tienda")
def tablero(usuario: AdminNegocio, db: Sesion):
    return servicio_resumen.tablero(db, usuario.tienda_id)


@router.get("/mi-cuenta/resumen", response_model=ResumenMiCuenta, summary="Tu crédito y el próximo pago")
def mi_cuenta(identidad: ClienteActual, db: Sesion):
    tienda_id, cliente_id = identidad
    return servicio_resumen.mi_cuenta(db, tienda_id, cliente_id)


@router.get("/mi-cuenta/compras", response_model=list[CompraRespuesta], summary="Tus compras y cronogramas")
def mis_compras(
    identidad: ClienteActual,
    db: Sesion,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    tienda_id, cliente_id = identidad
    return servicio_compras.listar_propias(db, tienda_id, cliente_id, limite, desplazamiento)
