"""Carga o retira una historia de prueba de la tienda existente Bodega Don Rosendo."""
import argparse
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.tiempo import hoy_lima
from app.db.sesion import motor
from app.models import (
    Bitacora, Cliente, Compra, CondicionCredito, Cuota, DetalleCompra, EstadoCuenta, EstadoCuentaDetalle,
    Marca, Pago, Producto, Proveedor, Rol, Tienda, Usuario,
)
from app.models.enumeraciones import AccionBitacora, EntidadBitacora, RolCodigo
from app.schemas.schemas_auth import UsuarioActual
from app.schemas.schemas_catalogos import MarcaCrear, ProveedorCrear
from app.schemas.schemas_clientes import ClienteCrear
from app.schemas.schemas_compras import CompraCrear
from app.schemas.schemas_productos import ProductoCrear
from app.services import (
    servicio_bitacora, servicio_catalogo, servicio_clientes, servicio_compras, servicio_estados_cuenta, servicio_pagos,
    servicio_productos,
)

TIENDA_DEMO = "Bodega Don Rosendo"
ORIGEN = "demo_don_rosendo_2026"
CLAVE_DEMO = "DonRosendo26"
CLIENTES = (
    ("ana", "Ana", "Quispe"), ("jorge", "Jorge", "Salazar"), ("rosa", "Rosa", "Montoya"),
    ("mario", "Mario", "Huamán"), ("lucia", "Lucía", "Rojas"), ("ines", "Inés", "Vega"),
    ("diego", "Diego", "Chávez"), ("pilar", "Pilar", "León"), ("elena", "Elena", "Torres"),
)
PRODUCTOS = (
    ("ARR", "Arroz extra 5 kg", "22.80", "24.00", 0),
    ("ACE", "Aceite vegetal 1 L", "9.40", "10.00", 0),
    ("LCH", "Leche evaporada, paquete de 6", "23.00", "25.00", 1),
    ("AVN", "Avena 1 kg", "6.90", "7.50", 1),
    ("JAB", "Jabón para ropa, paquete de 3", "7.90", "8.50", 2),
    ("DET", "Detergente familiar 4 kg", "36.50", "40.00", 2),
)
# Cliente, fecha de compra, producto, cantidad y número de cuotas; 0 indica fin de mes.
COMPRAS = (
    (0, "09-15", 0, 3, 3), (0, "09-15", 1, 2, 0), (1, "09-15", 5, 3, 0), (2, "09-17", 2, 4, 0),
    (3, "09-23", 3, 5, 0), (4, "10-04", 0, 3, 2), (5, "10-12", 4, 4, 0), (7, "10-18", 1, 6, 0),
    (8, "10-18", 5, 2, 2), (0, "10-27", 2, 2, 0), (1, "11-02", 3, 5, 0), (2, "11-03", 5, 2, 3),
    (3, "11-07", 0, 4, 0), (4, "11-10", 2, 4, 0), (5, "11-12", 1, 4, 0), (6, "11-14", 5, 2, 3),
    (7, "11-16", 4, 6, 0), (8, "11-17", 2, 3, 0),
)


class SesionDemo(Session):
    def commit(self) -> None:
        # Los servicios conservan su comportamiento; el comando confirma una sola vez al salir de begin().
        self.flush()


def _crear_demo(db: Session, tienda: Tienda, admin: Usuario) -> dict[str, list[int]]:
    actor = UsuarioActual(id_usuario=admin.id_usuario, username=admin.username, rol=RolCodigo.ADMIN_NEG,
                         tienda_id=tienda.id_tienda, id_cliente=None)
    tienda_id = tienda.id_tienda
    unidad = next((u for u in servicio_catalogo.listar_unidades(db) if u.codigo == "UND"), None)
    if unidad is None:
        raise ValueError("Ejecuta primero python -m app.db.seeds para cargar las unidades y monedas.")
    proveedor = servicio_catalogo.crear_proveedor(db, tienda_id, ProveedorCrear(razon_social="Distribuidora Rosendo (demo)"))
    marcas = [servicio_catalogo.crear_marca(db, tienda_id, MarcaCrear(nombre=f"{marca} (demo)"))
              for marca in ("Buen Campo", "La Granja", "Casa Limpia")]
    productos = [servicio_productos.crear(db, tienda_id, ProductoCrear(
        codigo=f"DEMO-{codigo}", nombre=nombre, unidad_id=unidad.id_unidad, marca_id=marcas[indice].id_marca,
        proveedor_id=proveedor.id_proveedor, precio_contado=contado, precio_lista=credito,
        permite_fin_de_mes=True, permite_cuotas=True,
    ), actor) for codigo, nombre, contado, credito, indice in PRODUCTOS]

    clientes = [servicio_clientes.crear(db, tienda_id, ClienteCrear.model_validate({
        "tipo_documento": "DNI", "numero_documento": f"990602{indice + 1:02}", "usuario": f"demo.{alias}",
        "nombres": nombres, "apellidos": apellidos, "password": CLAVE_DEMO,
        "condicion": {
            "moneda": "USD" if alias == "elena" else "PEN", "limite_credito": "500.00" if alias == "elena" else "900.00",
            "tasa_compensatoria": {"tipo": "EFECTIVA", "tasa_pct": "3", "plazo_tasa": "MENSUAL"},
            "tasa_moratoria": {"tipo": "NOMINAL", "tasa_pct": "12", "plazo_tasa": "ANUAL", "capitalizacion": "DIARIA"},
            "max_meses": 6, "dia_corte": 20, "hora_corte": "18:00", "dia_pago": 26, "vigente_desde": "2026-09-01",
        },
    }), actor) for indice, (alias, nombres, apellidos) in enumerate(CLIENTES)]
    compras = [servicio_compras.registrar(db, tienda_id, CompraCrear(
        cliente_id=clientes[c].id_cliente, modalidad="CUOTAS" if cuotas else "FIN_DE_MES", num_cuotas=cuotas or None,
        items=[{"producto_id": productos[p].id_producto, "cantidad": cantidad}],
        fecha_hora_compra=datetime.fromisoformat(f"2026-{fecha}T13:00:00"),
    ), actor) for c, fecha, p, cantidad, cuotas in COMPRAS]

    ids_clientes = [c.id_cliente for c in clientes]
    estados = [e for mes in (9, 10, 11) for e in servicio_estados_cuenta.generar(
        db, tienda_id, admin.id_usuario, 2026, mes, clientes_objetivo=ids_clientes,
    )]
    cobros = []
    for c, fecha in ((0, date(2026, 9, 26)), (1, date(2026, 10, 2))):
        estado = next(e for e in estados if e.cliente_id == ids_clientes[c] and e.mes == 9)
        _, exigible = servicio_pagos.calcular_exigible(db, estado.id_estado_cuenta, fecha, tienda_id=tienda_id)
        _, pago, _ = servicio_pagos.registrar_pago(
            db, estado.id_estado_cuenta, admin.id_usuario, exigible.total_exigible, fecha, tienda_id,
        )
        cobros.append(pago.id_pago)
    return {
        "usuarios": [db.get(Cliente, c.id_cliente).usuario_id for c in clientes],
        "clientes": ids_clientes, "condiciones": [c.condicion.id_condicion for c in clientes],
        "compras": [c.id_compra for c in compras], "estados": [e.id_estado_cuenta for e in estados], "pagos": cobros,
        "productos": [p.id_producto for p in productos], "marcas": [m.id_marca for m in marcas],
        "proveedores": [proveedor.id_proveedor],
    }


def _limpiar_demo(db: Session, marca: Bitacora) -> None:
    ids = marca.detalle["ids"]
    db.scalars(select(Cliente.id_cliente).where(Cliente.id_cliente.in_(ids["clientes"]))
               .order_by(Cliente.id_cliente).with_for_update()).all()
    # Restricciones de la base impiden retirar una fila si existe actividad ajena al conjunto demo que la referencia.
    for modelo, columna, valores in (
        (Pago, Pago.id_pago, ids["pagos"]),
        (EstadoCuentaDetalle, EstadoCuentaDetalle.estado_cuenta_id, ids["estados"]),
        (EstadoCuenta, EstadoCuenta.id_estado_cuenta, ids["estados"]),
        (Cuota, Cuota.compra_id, ids["compras"]),
        (DetalleCompra, DetalleCompra.compra_id, ids["compras"]),
        (Compra, Compra.id_compra, ids["compras"]),
        (CondicionCredito, CondicionCredito.id_condicion, ids["condiciones"]),
        (Cliente, Cliente.id_cliente, ids["clientes"]),
        (Producto, Producto.id_producto, ids["productos"]),
        (Marca, Marca.id_marca, ids["marcas"]),
        (Proveedor, Proveedor.id_proveedor, ids["proveedores"]),
    ):
        db.execute(delete(modelo).where(columna.in_(valores)))
    entidades = ((EntidadBitacora.USUARIO, "usuarios"), (EntidadBitacora.CLIENTE, "clientes"),
                (EntidadBitacora.COMPRA, "compras"), (EntidadBitacora.ESTADO_CUENTA, "estados"),
                (EntidadBitacora.PAGO, "pagos"), (EntidadBitacora.PRODUCTO, "productos"))
    db.execute(delete(Bitacora).where(or_(
        Bitacora.id_bitacora == marca.id_bitacora, Bitacora.usuario_id.in_(ids["usuarios"]),
        *(and_(Bitacora.entidad == entidad, Bitacora.entidad_id.in_(ids[clave])) for entidad, clave in entidades),
    )))
    db.execute(delete(Usuario).where(Usuario.id_usuario.in_(ids["usuarios"])))


def operar_demo(*, limpiar: bool = False, motor_db=motor) -> str:
    with SesionDemo(bind=motor_db, autoflush=False) as db, db.begin():
        tiendas = db.scalars(select(Tienda).where(Tienda.nombre_comercial == TIENDA_DEMO).with_for_update()).all()
        if len(tiendas) != 1:
            raise ValueError(f"Debe existir exactamente una tienda llamada {TIENDA_DEMO}.")
        tienda = tiendas[0]
        marca = db.scalar(select(Bitacora).where(
            Bitacora.entidad == EntidadBitacora.TIENDA, Bitacora.entidad_id == tienda.id_tienda,
            Bitacora.detalle["origen"].as_string() == ORIGEN,
        ))
        if limpiar:
            if marca is None:
                return "La tienda no tiene datos de esta demo."
            _limpiar_demo(db, marca)
            return "Datos de demostración retirados."
        if marca is not None:
            return "Los datos de demostración ya están cargados."
        if not tienda.activo or hoy_lima() < date(2026, 11, 21):
            raise ValueError("La tienda debe estar activa y haber pasado el corte del 20 de noviembre de 2026.")
        admin = db.scalar(select(Usuario).join(Usuario.rol).where(
            Usuario.tienda_id == tienda.id_tienda, Usuario.activo.is_(True), Rol.codigo == RolCodigo.ADMIN_NEG,
        ).order_by(Usuario.id_usuario).limit(1))
        if admin is None:
            raise ValueError("La tienda no tiene un administrador activo.")
        ids = _crear_demo(db, tienda, admin)
        servicio_bitacora.registrar(db, admin.id_usuario, EntidadBitacora.TIENDA, tienda.id_tienda,
                                   AccionBitacora.MODIFICACION, {"origen": ORIGEN, "ids": ids})
        return f"Demo cargada: {len(ids['clientes'])} clientes, {len(ids['productos'])} productos, " \
               f"{len(ids['compras'])} compras, {len(ids['estados'])} estados y {len(ids['pagos'])} pagos."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limpiar", action="store_true", help="Retira solo el conjunto de datos de la demo.")
    try:
        print(operar_demo(limpiar=parser.parse_args().limpiar))
    except HTTPException as error:
        parser.exit(1, f"No se cargó la demo: {error.detail}\n")
    except servicio_pagos.ErrorPago as error:
        parser.exit(1, f"No se cargó la demo: {error.detalle}\n")
    except IntegrityError:
        parser.exit(1, "Se conservó la base. Hay datos relacionados o una coincidencia con los datos de la demo.\n")
    except ValueError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
