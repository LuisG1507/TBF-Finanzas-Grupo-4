from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencias import admin_de_negocio, requiere_rol
from app.db.sesion import obtener_sesion
from app.models.enumeraciones import RolCodigo
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_clientes import ClienteActualizar, ClienteCrear, ClienteRespuesta, CondicionCrear, CondicionRespuesta, NuevaPassword
from app.services import servicio_clientes

router = APIRouter(tags=["Clientes"])


@router.post("/clientes", response_model=ClienteRespuesta, status_code=status.HTTP_201_CREATED, summary="Alta de un cliente con su acceso y su condición de crédito")
def crear_cliente(datos: ClienteCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_clientes.crear(db, usuario.tienda_id, datos, usuario)


@router.get("/clientes", response_model=list[ClienteRespuesta], summary="Lista los clientes de tu tienda, con su condición de crédito vigente")
def listar_clientes(
    activo: bool | None = Query(default=None, description="true = solo activos, false = solo dados de baja"),
    buscar: str | None = Query(default=None, description="Texto a buscar en el nombre, los apellidos o el documento"),
    limite: int = Query(default=50, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
    usuario: UsuarioActual = Depends(admin_de_negocio),
    db: Session = Depends(obtener_sesion),
):
    return servicio_clientes.listar(db, usuario.tienda_id, activo, buscar, limite, desplazamiento)


@router.get("/mi-perfil", response_model=ClienteRespuesta, summary="Mis datos y mi condición de crédito vigente (cliente)")
def mi_perfil(usuario: UsuarioActual = Depends(requiere_rol(RolCodigo.CLIENTE)), db: Session = Depends(obtener_sesion)):
    if usuario.id_cliente is None or usuario.tienda_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu usuario no está asociado a ningún cliente.")
    return servicio_clientes.mi_perfil(db, usuario.tienda_id, usuario.id_cliente)


@router.get("/clientes/{id_cliente}", response_model=ClienteRespuesta, summary="Un cliente de tu tienda")
def ver_cliente(id_cliente: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_clientes.obtener(db, usuario.tienda_id, id_cliente)


@router.patch("/clientes/{id_cliente}", response_model=ClienteRespuesta, summary="Modifica los datos generales de un cliente; solo cambia lo que se envía")
def modificar_cliente(
    id_cliente: int, datos: ClienteActualizar, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)
):
    return servicio_clientes.actualizar(db, usuario.tienda_id, id_cliente, datos, usuario)


@router.put(
    "/clientes/{id_cliente}/condicion",
    response_model=ClienteRespuesta,
    summary="Cambia la condición de crédito: se guarda una versión nueva y la anterior queda en el historial",
)
def cambiar_condicion(
    id_cliente: int, datos: CondicionCrear, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)
):
    return servicio_clientes.cambiar_condicion(db, usuario.tienda_id, id_cliente, datos, usuario)


@router.get("/clientes/{id_cliente}/condiciones", response_model=list[CondicionRespuesta], summary="Historial de condiciones de crédito del cliente (la más reciente primero)")
def historial_condiciones(id_cliente: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_clientes.historial_condiciones(db, usuario.tienda_id, id_cliente)


@router.post("/clientes/{id_cliente}/baja", response_model=ClienteRespuesta, summary="Da de baja a un cliente: ya no podrá entrar")
def dar_de_baja_cliente(id_cliente: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_clientes.dar_de_baja(db, usuario.tienda_id, id_cliente, usuario)


@router.post("/clientes/{id_cliente}/alta", response_model=ClienteRespuesta, summary="Reactiva a un cliente dado de baja")
def reactivar_cliente(id_cliente: int, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    return servicio_clientes.reactivar(db, usuario.tienda_id, id_cliente, usuario)


@router.put("/clientes/{id_cliente}/password", status_code=status.HTTP_204_NO_CONTENT, summary="Reinicia la contraseña de un cliente")
def reiniciar_password(id_cliente: int, datos: NuevaPassword, usuario: UsuarioActual = Depends(admin_de_negocio), db: Session = Depends(obtener_sesion)):
    servicio_clientes.reiniciar_password(db, usuario.tienda_id, id_cliente, datos.nueva_password, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
