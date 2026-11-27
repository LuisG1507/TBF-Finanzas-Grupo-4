"""Prueba de flujo en Chrome centrada en el cobro: deuda vencida, mora, rechazo del pago parcial,
pago completo con excedente, efecto en la base y lo que ve el cliente antes y después.

Desde la raíz del repositorio: python -m datos_prueba.pruebas_http.flujo_pagos_navegador
Usa un esquema PostgreSQL temporal (se borra al terminar) y la demo de Bodega Don Rosendo.
"""
import json
from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path
from subprocess import CREATE_NO_WINDOW, DEVNULL, Popen
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from app.core.configuracion import configuracion
from app.db.base import Base
from app.db.demo import CLAVE_DEMO, operar_demo
from app.db.seeds import cargar_seeds
from app.db.sesion import SesionLocal
from app.models import Bitacora, Cliente, EstadoCuenta, Pago
from app.models.enumeraciones import EntidadBitacora, EstadoCuentaEstado
from datos_prueba.pruebas_http.frontend_real import (
    NAVEGADOR, Navegador, conteos, detener, esperar_recurso, iniciar_servidores,
)

D = Decimal
FECHA_PAGO = "2026-10-01"  # cinco días después del vencimiento del 26 de setiembre


def _api(api, metodo, ruta, token=None, datos=None, formulario=None):
    cuerpo, cabeceras = None, {}
    if formulario is not None:
        cuerpo = urlencode(formulario).encode()
    elif datos is not None:
        cuerpo, cabeceras["Content-Type"] = json.dumps(datos).encode(), "application/json"
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    with urlopen(Request(api + "/api/v1" + ruta, data=cuerpo, headers=cabeceras, method=metodo), timeout=10) as respuesta:
        return json.load(respuesta)


def _crear_tienda(api, admin, clave):
    token = _api(api, "POST", "/auth/login", formulario={"username": admin, "password": clave})["access_token"]
    _api(api, "POST", "/tiendas", token, {
        "ruc": "20512345678", "razon_social": "Bodega Don Rosendo S.A.C.", "nombre_comercial": "Bodega Don Rosendo",
        "giro": "bodega", "admin_username": "negocio.pagos", "admin_password": clave,
    })


def _estado_vencido_de_rosa(motor):
    with Session(motor) as sesion:
        rosa = sesion.scalars(select(Cliente).where(Cliente.nombres == "Rosa")).one()
        return sesion.scalars(
            select(EstadoCuenta).where(EstadoCuenta.cliente_id == rosa.id_cliente, EstadoCuenta.estado != EstadoCuentaEstado.PAGADO)
            .order_by(EstadoCuenta.fecha_pago)
        ).first()


def _monto_en_pantalla(n, etiqueta):
    """Lee el importe de una fila «etiqueta … S/ 0.00» del recuadro del estado de cuenta."""
    texto = n.evaluar(f"""(() => {{
      const fila = Array.from(document.querySelectorAll('main *')).find(e =>
        e.children.length >= 2 && e.firstElementChild?.innerText?.trim() === {json.dumps(etiqueta)});
      return fila ? fila.lastElementChild.innerText : null }})()""")
    assert texto, f"No se encontró la fila {etiqueta}"
    return D(texto.replace("S/", "").replace("US$", "").replace(",", "").strip())


def probar(n, api, motor, clave):
    _crear_tienda(api, "verificador.pagos", clave)
    assert "9 clientes" in operar_demo(motor_db=motor)
    estado = _estado_vencido_de_rosa(motor)
    assert estado is not None, "La demo debe dejar a Rosa con un estado de cuenta vencido"

    # 1. El cliente ve su deuda vencida y no puede entrar a pantallas del negocio.
    n.ir("/login")
    n.entrar("demo.rosa", CLAVE_DEMO, "Mi cuenta")
    n.texto("Mis estados de cuenta", "main")
    n.texto("Vencido", "main")
    n.comando("Page.navigate", url=n.url + "/admin-negocio/pagos/nuevo")
    n.esperar("location.pathname === '/cliente/mi-cuenta'", "Un cliente no entra a Registrar pago")
    n.salir()

    # 2. El negocio cobra con atraso: aparecen la mora y el total, y se rechaza el pago incompleto.
    n.entrar("negocio.pagos", clave, "Resumen")
    n.ir("/admin-negocio/pagos/nuevo")
    n.opcion("#cliente_pago", "Rosa Montoya")
    n.llenar("#fecha_pago", FECHA_PAGO)
    n.texto("Días de mora", "main")
    n.esperar("""Array.from(document.querySelectorAll('main *')).some(e => e.children.length >= 2
      && e.firstElementChild?.innerText?.trim() === 'Días de mora' && e.lastElementChild.innerText.trim() === '5')""",
              "Del 26/09 al 01/10 son 5 días de mora (30/360)")
    total = _monto_en_pantalla(n, "Total a pagar")
    mora = _monto_en_pantalla(n, "Interés moratorio")
    assert mora > 0 and total > estado.total_capital, (mora, total)

    n.llenar("#monto", str(total - D("0.01")))
    n.boton("Registrar pago", "main")
    n.texto("no se aceptan pagos parciales", "[role='alert']")
    with Session(motor) as sesion:
        assert sesion.scalar(select(func.count()).select_from(Pago).where(Pago.estado_cuenta_id == estado.id_estado_cuenta)) == 0
    n.comprobaciones += 1

    # 3. Pago completo con S/ 20 de más: se aplica en orden y se informa el excedente.
    n.llenar("#monto", str(total + 20))
    n.boton("Registrar pago", "main")
    n.texto("Pago registrado", "main")
    n.texto("de excedente.", "main")
    n.texto("20.00", "main")

    with Session(motor) as sesion:
        pago = sesion.scalars(select(Pago).where(Pago.estado_cuenta_id == estado.id_estado_cuenta)).one()
        pagado = sesion.get(EstadoCuenta, estado.id_estado_cuenta)
        assert pagado.estado == EstadoCuentaEstado.PAGADO
        assert pago.monto_pagado == total, "Solo se guarda lo aplicado, no el excedente"
        assert pago.monto_mora_aplicado == mora
        assert pago.monto_mora_aplicado + pago.monto_interes_comp_aplicado + pago.monto_capital_aplicado <= pago.monto_pagado
        assert sesion.scalar(select(func.count()).select_from(Bitacora).where(
            Bitacora.entidad == EntidadBitacora.PAGO, Bitacora.entidad_id == pago.id_pago)) == 1
    n.comprobaciones += 5
    n.salir()

    # 4. El cliente ve el estado pagado.
    n.entrar("demo.rosa", CLAVE_DEMO, "Mi cuenta")
    n.texto("Pagado", "main")
    n.salir()

    # 5. En el teléfono, el menú lateral se abre y lleva a otra pantalla.
    n.comando("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    n.entrar("negocio.pagos", clave, "Resumen")
    n.esperar("Boolean(document.querySelector('[aria-label=\"Abrir menú\"]'))", "Botón de menú en el teléfono")
    n.evaluar("document.querySelector('[aria-label=\"Abrir menú\"]').click()")
    n.esperar("document.querySelector('[aria-label=\"Abrir menú\"]').getAttribute('aria-expanded') === 'true'", "Menú abierto")
    n.evaluar("Array.from(document.querySelectorAll('#menu-principal a')).find(a => a.innerText.includes('Estados de cuenta')).click()")
    n.texto("Estados de cuenta", "h1")
    n.esperar("document.documentElement.scrollWidth <= window.innerWidth + 1", "Sin desplazamiento horizontal de la página")
    n.comando("Emulation.clearDeviceMetricsOverride")

    # 6. Retirar la demo no debe borrar un pago registrado después: la base se conserva.
    try:
        operar_demo(limpiar=True, motor_db=motor)
    except IntegrityError:
        pass
    else:
        raise AssertionError("La demo no debía retirarse con un pago posterior que la referencia")
    with Session(motor) as sesion:
        assert sesion.scalar(select(func.count()).select_from(Pago).where(Pago.estado_cuenta_id == estado.id_estado_cuenta)) == 1
    n.comprobaciones += 2


def main():
    if not NAVEGADOR.is_file():
        raise SystemExit("Indica el ejecutable de Chrome con TBF_NAVEGADOR.")
    esquema = "prueba_pagos_" + uuid4().hex
    base = create_engine(configuracion.url_base_datos)
    antes = conteos(base)
    with base.begin() as conexion:
        conexion.execute(CreateSchema(esquema))
    try:
        with ExitStack() as recursos:
            motor = create_engine(configuracion.url_base_datos, connect_args={"options": f"-csearch_path={esquema}"})
            recursos.callback(motor.dispose)
            Base.metadata.create_all(motor)
            SesionLocal.configure(bind=motor)
            clave = uuid4().hex
            configuracion.admin_sistema_usuario = "verificador.pagos"
            configuracion.admin_sistema_password = clave
            cargar_seeds()
            api, frontend = iniciar_servidores(recursos)
            perfil = Path(recursos.enter_context(TemporaryDirectory(ignore_cleanup_errors=True)))
            chrome = Popen(
                [str(NAVEGADOR), "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking",
                 "--window-size=1320,900", "--remote-debugging-port=0", f"--user-data-dir={perfil}", "about:blank"],
                stdout=DEVNULL, stderr=DEVNULL, creationflags=CREATE_NO_WINDOW,
            )
            recursos.callback(detener, chrome)
            puerto = esperar_recurso(lambda: (perfil / "DevToolsActivePort").read_text(encoding="utf-8").splitlines()[0])
            with urlopen(f"http://127.0.0.1:{puerto}/json/list", timeout=5) as respuesta:
                url_ws = next(p["webSocketDebuggerUrl"] for p in json.load(respuesta) if p["type"] == "page")
            with connect(url_ws) as conexion:
                navegador = Navegador(conexion, frontend)
                probar(navegador, api, motor, clave)
                assert not navegador.errores, navegador.errores
                try:
                    navegador.comando("Browser.close")
                except ConnectionClosed:
                    pass
    finally:
        with base.begin() as conexion:
            conexion.execute(DropSchema(esquema, cascade=True))
        assert conteos(base) == antes, "La base compartida debe conservar sus datos"
        base.dispose()
    print(f"RESULTADO: {navegador.comprobaciones} comprobaciones del flujo de pagos en Chrome, con API y base reales.")


if __name__ == "__main__":
    main()
