"""Prueba en Chrome el frontend conectado a la API real y a PostgreSQL.

Desde Backend-Grupo4: python -m datos_prueba.pruebas_http.frontend_real
Requiere npm install en frontend-ts. TBF_NAVEGADOR permite indicar el ejecutable de Chrome.
"""
import json
import os
import socket
from contextlib import ExitStack
from pathlib import Path
from subprocess import CREATE_NO_WINDOW, DEVNULL, Popen, TimeoutExpired
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import uvicorn
from sqlalchemy import create_engine, func, select
from sqlalchemy.schema import CreateSchema, DropSchema
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from app.core.configuracion import configuracion
from app.db.base import Base
from app.db.demo import CLAVE_DEMO, operar_demo
from app.db.seeds import cargar_seeds
from app.db.sesion import SesionLocal
from app.main import app
from app.models import Cliente, Compra, EstadoCuenta, Pago, Producto, Tienda, Usuario

RAIZ = Path(__file__).resolve().parents[2]
NAVEGADOR = Path(os.environ.get("TBF_NAVEGADOR", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))


class Navegador:
    def __init__(self, conexion, url):
        self.conexion = conexion
        self.url = url
        self.secuencia = 0
        self.comprobaciones = 0
        self.errores = []
        self.comando("Runtime.enable")
        self.comando("Page.enable")

    def comando(self, metodo, **parametros):
        self.secuencia += 1
        self.conexion.send(json.dumps({"id": self.secuencia, "method": metodo, "params": parametros}))
        while True:
            datos = json.loads(self.conexion.recv(timeout=10))
            if datos.get("method") == "Runtime.exceptionThrown":
                detalle = datos["params"]["exceptionDetails"]
                self.errores.append(detalle.get("exception", {}).get("description", detalle["text"]))
            if datos.get("id") == self.secuencia:
                if "error" in datos:
                    raise AssertionError(datos["error"])
                return datos["result"]

    def evaluar(self, javascript):
        resultado = self.comando("Runtime.evaluate", expression=javascript, returnByValue=True)
        if "exceptionDetails" in resultado:
            raise AssertionError(resultado["exceptionDetails"])
        return resultado["result"].get("value")

    def esperar(self, condicion, descripcion):
        limite = monotonic() + 10
        while monotonic() < limite:
            if self.evaluar(condicion):
                self.comprobaciones += 1
                return
            sleep(0.08)
        texto = self.evaluar("document.body?.innerText?.slice(0, 900)")
        raise AssertionError(f"{descripcion}; contenido visible: {texto}")

    def ir(self, ruta):
        self.comando("Page.navigate", url=self.url + ruta)
        self.esperar("location.pathname === " + json.dumps(ruta) + " && Boolean(document.querySelector('#root'))", ruta)

    def texto(self, contenido, selector="body"):
        self.esperar(
            f"Array.from(document.querySelectorAll({json.dumps(selector)})).some(e => e.innerText.includes({json.dumps(contenido)}))",
            f"Debía aparecer {contenido}",
        )

    def llenar(self, selector, valor):
        argumento = json.dumps([selector, valor], ensure_ascii=False)
        self.esperar("Boolean(document.querySelector(" + json.dumps(selector) + "))", selector)
        self.evaluar(f"""((args) => {{
          const elemento = document.querySelector(args[0]);
          const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(elemento), 'value').set;
          setter.call(elemento, args[1]);
          elemento.dispatchEvent(new Event('input', {{ bubbles: true }}));
          elemento.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }})({argumento})""")

    def boton(self, etiqueta, contenedor="body"):
        arg = json.dumps([etiqueta, contenedor], ensure_ascii=False)
        buscar = f"""((args) => Array.from(document.querySelectorAll(args[1] + ' button'))
          .find(b => b.innerText.trim() === args[0] && !b.disabled))({arg})"""
        self.esperar("Boolean(" + buscar + ")", f"Botón habilitado: {etiqueta}")
        self.evaluar(buscar + ".click()")

    def fila(self, texto):
        return f"Array.from(document.querySelectorAll('tbody tr')).find(e => e.innerText.includes({json.dumps(texto)}))"

    def accion_fila(self, fila, boton):
        fila = self.fila(fila)
        buscar = f"""Array.from(({fila})?.querySelectorAll('button') ?? [])
          .find(e => e.innerText.trim() === {json.dumps(boton)} && !e.disabled)"""
        self.esperar("Boolean(" + buscar + ")", boton)
        self.evaluar("(" + buscar + ").click()")

    def opcion(self, selector, texto):
        buscar = f"Array.from(document.querySelector({json.dumps(selector)})?.options ?? []).find(o => o.text.includes({json.dumps(texto)}))"
        self.esperar("Boolean(" + buscar + ")", f"Opción {texto}")
        self.llenar(selector, self.evaluar("(" + buscar + ").value"))

    def entrar(self, usuario, clave, titulo=None):
        self.texto("Inicia sesión", "h1")
        self.llenar("#usuario", usuario)
        self.llenar("#clave", clave)
        self.boton("Ingresar")
        if titulo:
            self.texto(titulo, "h1")

    def salir(self):
        self.boton("Cerrar sesión")
        self.texto("Inicia sesión", "h1")
        self.esperar("sessionStorage.getItem('bizon-token') === null && sessionStorage.getItem('tbf-token') === null", "JWT eliminado")


def esperar_recurso(leer):
    limite = monotonic() + 16
    while monotonic() < limite:
        try:
            dato = leer()
            if dato:
                return dato
        except (OSError, ValueError, IndexError):
            pass
        sleep(0.1)
    raise AssertionError("No inició uno de los servidores de la prueba")


def puerto_libre():
    with socket.socket() as enlace:
        enlace.bind(("127.0.0.1", 0))
        return enlace.getsockname()[1]


def detener(proceso):
    if proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=8)
        except TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=8)


def iniciar_servidores(recursos):
    enlace = recursos.enter_context(socket.socket())
    enlace.bind(("127.0.0.1", 0))
    enlace.listen()
    api = f"http://127.0.0.1:{enlace.getsockname()[1]}"
    servidor = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
    hilo = Thread(target=servidor.run, kwargs={"sockets": [enlace]}, daemon=True)
    hilo.start()

    def detener_api():
        servidor.should_exit = True
        hilo.join(timeout=8)

    recursos.callback(detener_api)
    esperar_recurso(lambda: servidor.started)
    puerto = puerto_libre()
    frontend = f"http://127.0.0.1:{puerto}"
    vite = Popen(
        ["node", "./node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", str(puerto), "--strictPort"],
        cwd=RAIZ / "frontend-ts", env={**os.environ, "TBF_API_PROXY": api},
        stdout=DEVNULL, stderr=DEVNULL, creationflags=CREATE_NO_WINDOW,
    )
    recursos.callback(detener, vite)

    def vite_listo():
        with urlopen(frontend, timeout=2) as respuesta:
            return respuesta.status == 200

    esperar_recurso(vite_listo)
    return api, frontend


def preparar_cliente_retroactivo(api, usuario, clave):
    login = Request(api + "/api/v1/auth/login", data=urlencode({"username": usuario, "password": clave}).encode())
    with urlopen(login, timeout=5) as respuesta:
        token = json.load(respuesta)["access_token"]
    datos = {
        "tipo_documento": "DNI", "numero_documento": "98989801", "nombres": "Nora", "apellidos": "Navegador",
        "password": clave,
        "condicion": {
            "moneda": "PEN", "limite_credito": "1000.00", "max_meses": 3, "dia_corte": 20,
            "hora_corte": "18:00", "dia_pago": 26, "vigente_desde": "2026-09-01",
            "tasa_compensatoria": {"tipo": "EFECTIVA", "tasa_pct": "3", "plazo_tasa": 30},
            "tasa_moratoria": {"tipo": "NOMINAL", "tasa_pct": "12", "plazo_tasa": 360, "capitalizacion": 1},
        },
    }
    solicitud = Request(api + "/api/v1/clientes", data=json.dumps(datos).encode(), headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {token}",
    })
    with urlopen(solicitud, timeout=5) as respuesta:
        if respuesta.status != 201:
            raise AssertionError("No se preparó el cliente para la compra retroactiva")


def probar(navegador, api, motor, clave):
    n = navegador
    n.ir("/login")
    n.esperar("document.title === 'Bizon'", "Marca en el título de la pestaña")
    n.texto("Bizon")
    n.entrar("verificador.frontend", "invalida")
    n.texto("Usuario o contraseña incorrectos.", "[role='alert']")
    n.entrar("verificador.frontend", clave, "Tiendas")
    n.texto("Bizon", "aside")
    n.evaluar("""
        sessionStorage.setItem('tbf-token', sessionStorage.getItem('bizon-token'));
        sessionStorage.removeItem('bizon-token');
        localStorage.setItem('tbf-tema', 'oscuro');
        localStorage.removeItem('bizon-tema');
    """)
    n.comando("Page.reload")
    n.texto("Tiendas", "h1")
    n.esperar("Boolean(sessionStorage.getItem('bizon-token')) && sessionStorage.getItem('tbf-token') === null", "La sesión previa sigue vigente")
    n.esperar("document.documentElement.dataset.tema === 'oscuro' && localStorage.getItem('bizon-tema') === 'oscuro' && localStorage.getItem('tbf-tema') === null", "La preferencia anterior se conserva")
    n.boton("Nueva tienda")
    for selector, valor in {
        "#ruc": "20765432123", "#giro": "Bodega", "#razon_social": "Rosendo S.A.C.",
        "#nombre_comercial": "Bodega Don Rosendo", "#usuario_admin": "negocio.frontend", "#clave_admin": clave,
    }.items():
        n.llenar(selector, valor)
    n.boton("Crear tienda")
    n.texto("Bodega Don Rosendo", "tbody tr")
    n.accion_fila("Bodega Don Rosendo", "Dar de baja")
    n.texto("Dada de baja", "tbody tr")
    n.accion_fila("Bodega Don Rosendo", "Reactivar")
    n.esperar("(" + n.fila("Bodega Don Rosendo") + ")?.innerText.includes('Activa')", "Tienda reactivada")
    n.salir()

    resultado_demo = operar_demo(motor_db=motor)
    assert "9 clientes" in resultado_demo
    preparar_cliente_retroactivo(api, "negocio.frontend", clave)
    n.entrar("negocio.frontend", clave, "Resumen")
    n.texto("Saldo por cobrar", "main")
    n.texto("S/", "main")
    n.comando("Page.navigate", url=n.url + "/admin-sistema/tiendas")
    n.esperar("location.pathname === '/admin-negocio'", "Un negocio redirige a su ruta autorizada")

    n.ir("/admin-negocio/productos")
    n.texto("Arroz extra 5 kg", "tbody tr")
    n.boton("Nueva marca")
    n.llenar("#catalogo-nombre", "Marca navegador")
    n.boton("Guardar")
    n.esperar("!document.querySelector('[role=dialog]')", "Marca guardada")
    n.boton("Nuevo proveedor")
    n.llenar("#catalogo-nombre", "Proveedor navegador")
    n.boton("Guardar")
    n.esperar("!document.querySelector('[role=dialog]')", "Proveedor guardado")
    n.boton("Nuevo producto")
    for selector, valor in {
        "#codigo": "NAV01", "#nombre": "Producto navegador", "#precio_contado": "9.00", "#precio_lista": "10.00",
    }.items():
        n.llenar(selector, valor)
    n.opcion("#unidad_id", "Unidad")
    n.opcion("#marca_id", "Marca navegador")
    n.opcion("#proveedor_id", "Proveedor navegador")
    n.evaluar("document.querySelector('[name=permite_cuotas]').click()")
    n.boton("Guardar producto")
    n.texto("Producto navegador", "tbody tr")
    n.texto("Marca navegador", "tbody tr")

    n.ir("/admin-negocio/clientes")
    n.boton("Nuevo cliente")
    for selector, valor in {
        "#numero_documento": "98989802", "#nombres": "Irene", "#apellidos": "Navegador",
        "#password": clave, "#tasa_compensatoria": "12", "#tasa_moratoria": "15",
        "#limite_credito": "200.00", "#max_meses": "3", "#dia_corte": "20", "#dia_pago": "26",
    }.items():
        n.llenar(selector, valor)
    n.boton("Guardar cliente")
    n.texto("Irene Navegador", "tbody tr")
    n.accion_fila("Irene Navegador", "Cambiar condiciones")
    n.llenar("#limite_credito", "250.00")
    n.boton("Guardar condiciones")
    n.esperar("!document.querySelector('[role=dialog]')", "Condición nueva guardada")
    n.accion_fila("Irene Navegador", "Historial")
    n.texto("Historial de condiciones", "[role='dialog']")
    n.texto("250.00", "[role='dialog']")
    n.comando("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)

    n.ir("/admin-negocio/compras/nueva")
    n.opcion("#cliente", "Nora Navegador")
    n.llenar("#fecha-compra", "2026-09-15T10:00")
    n.opcion("#producto", "Producto navegador")
    n.boton("Agregar")
    n.evaluar("Array.from(document.querySelectorAll('[name=modalidad]'))[1].click()")
    n.llenar("#num_cuotas", "3")
    n.boton("Simular compra")
    n.texto("Cronograma de pagos", "main")
    n.texto("11", "main")
    n.texto("26 dic 2026", "main")
    n.boton("Registrar compra")
    n.texto("Compra registrada", "main")

    n.llenar("#fecha-compra", "2026-09-15T11:00")
    n.boton("Agregar")
    n.evaluar("Array.from(document.querySelectorAll('[name=modalidad]'))[0].click()")
    n.boton("Simular compra")
    n.texto("Pago a fin de mes", "main")
    n.boton("Registrar compra")
    n.texto("Compra registrada", "main")

    n.ir("/admin-negocio/estados-cuenta")
    n.boton("Generar estados")
    n.llenar("#periodo-corte", "2026-09")
    n.boton("Generar")
    n.texto("Nora Navegador", "main")

    n.ir("/admin-negocio/pagos/nuevo")
    n.opcion("#cliente_pago", "Nora Navegador")
    n.llenar("#fecha_pago", "2026-10-02")
    n.texto("Días de mora", "main")
    n.llenar("#monto", "0.01")
    n.boton("Registrar pago", "main")
    n.texto("no se aceptan pagos parciales", "[role='alert']")
    n.llenar("#monto", "100.00")
    n.boton("Registrar pago", "main")
    n.texto("Pago registrado", "main")
    n.texto("de excedente.", "main")

    n.salir()
    n.entrar("demo.elena", CLAVE_DEMO, "Mi cuenta")
    n.texto("US$", "main")
    n.texto("Cronograma de tu compra en cuotas", "main")
    n.texto("Mis estados de cuenta", "main")
    n.esperar("!document.querySelector('main').innerText.includes('Nora Navegador')", "El titular solo ve sus datos")
    n.evaluar("sessionStorage.setItem('bizon-token', 'expirado-de-prueba')")
    n.comando("Page.reload")
    n.texto("Inicia sesión", "h1")
    n.esperar("sessionStorage.getItem('bizon-token') === null", "El 401 invalida el JWT guardado")

    resultado_limpieza = operar_demo(limpiar=True, motor_db=motor)
    assert "retirados" in resultado_limpieza
    n.comprobaciones += 2


def conteos(motor):
    with motor.connect() as conexion:
        return tuple(conexion.scalar(select(func.count()).select_from(m)) for m in (
            Tienda, Usuario, Producto, Cliente, Compra, EstadoCuenta, Pago,
        ))


def main():
    if not NAVEGADOR.is_file():
        raise SystemExit("Indica el ejecutable de Chrome con TBF_NAVEGADOR.")
    esquema = "codex_prueba_frontend_" + uuid4().hex
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
            configuracion.admin_sistema_usuario = "verificador.frontend"
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
                paginas = json.load(respuesta)
            url_ws = next(p["webSocketDebuggerUrl"] for p in paginas if p["type"] == "page")
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
    print(f"RESULTADO: {navegador.comprobaciones + 2} comprobaciones en Chrome, con API y base reales.")


if __name__ == "__main__":
    main()
