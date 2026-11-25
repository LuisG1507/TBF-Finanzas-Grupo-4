from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import EstadoCompra, ModalidadCompra
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_compras import AnularCompra, CompraCrear, CompraResumen, CompraRespuesta, CreditoDisponibleRespuesta
from app.services import servicio_compras

router = APIRouter(tags=["Compras"])


@router.post("/compras/simular", response_model=CompraRespuesta, summary="Calcula una compra (cronograma incluido) sin guardarla; indica si excede el límite")
def simular_compra(datos: CompraCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_compras.simular(db, usuario.tienda_id, datos)


@router.post("/compras", response_model=CompraRespuesta, status_code=status.HTTP_201_CREATED, summary="Registra una compra a crédito de un cliente de tu tienda")
def registrar_compra(datos: CompraCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_compras.registrar(db, usuario.tienda_id, datos, usuario)


@router.get("/compras", response_model=list[CompraResumen], summary="Lista las compras de tu tienda, las más recientes primero")
def listar_compras(
    cliente_id: int | None = Query(default=None, gt=0),
    estado: EstadoCompra | None = Query(default=None),
    modalidad: ModalidadCompra | None = Query(default=None),
    desde: date | None = Query(default=None, description="Compras desde esta fecha (hora de Lima), inclusive"),
    hasta: date | None = Query(default=None, description="Compras hasta esta fecha (hora de Lima), inclusive"),
    limite: int = Query(default=50, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
    usuario: UsuarioActual = Depends(admin_de_negocio),
    db: Session = Depends(obtener_sesion),
):
    return servicio_compras.listar(db, usuario.tienda_id, cliente_id, estado, modalidad, desde, hasta, limite, desplazamiento)


@router.get("/compras/{id_compra}", response_model=CompraRespuesta, summary="Una compra con su detalle y su cronograma")
def ver_compra(id_compra: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_compras.obtener(db, usuario.tienda_id, id_compra)


@router.post("/compras/{id_compra}/anular", response_model=CompraRespuesta, summary="Anula una compra (solo si no tiene pagos ni figura en un estado de cuenta)")
def anular_compra(id_compra: int, datos: AnularCompra, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_compras.anular(db, usuario.tienda_id, id_compra, datos.motivo, usuario)


@router.get("/clientes/{id_cliente}/credito-disponible", response_model=CreditoDisponibleRespuesta, summary="Límite, capital pendiente y crédito disponible de un cliente")
def credito_disponible(id_cliente: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_compras.credito_disponible(db, usuario.tienda_id, id_cliente)
