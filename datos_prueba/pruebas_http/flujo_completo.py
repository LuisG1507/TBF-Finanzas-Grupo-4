"""Ejecuta el caso de Bizon por HTTP desde un esquema nuevo con Alembic.

Desde Backend-Grupo4: python -m datos_prueba.pruebas_http.flujo_completo
"""
import json
import socket
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from threading import Thread
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.core.configuracion import configuracion
from app.db.base import Base
from app.db.seeds import cargar_seeds
from app.db.sesion import SesionLocal
from app.main import app

D = Decimal
RAIZ = Path(__file__).resolve().parents[2]


class Api:
    def __init__(self, url):
        self.url = url + "/api/v1"
        self.comprobaciones = 0

    def comprobar(self, condicion, mensaje):
        if not condicion:
            raise AssertionError(mensaje)
        self.comprobaciones += 1

    def llamar(self, metodo, ruta, estado=200, *, token=None, datos=None):
        cabeceras = {"Accept": "application/json"}
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        cuerpo = None
        if datos is not None:
            if ruta == "/auth/login":
                cuerpo = urlencode(datos).encode()
                cabeceras["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                cuerpo = json.dumps(datos).encode()
                cabeceras["Content-Type"] = "application/json"
        peticion = Request(self.url + ruta, data=cuerpo, headers=cabeceras, method=metodo)
        try:
            with urlopen(peticion, timeout=10) as respuesta:
                codigo, bruto = respuesta.status, respuesta.read()
        except HTTPError as respuesta:
            codigo, bruto = respuesta.code, respuesta.read()
        self.comprobar(codigo == estado, f"{metodo} {ruta}: se esperaba HTTP {estado}, llegó {codigo}")
        return json.loads(bruto) if bruto else None

    def iniciar_sesion(self, usuario, clave, rol):
        respuesta = self.llamar("POST", "/auth/login", datos={"username": usuario, "password": clave})
        token = respuesta["access_token"]
        perfil = self.llamar("GET", "/auth/yo", token=token)
        self.comprobar(perfil["rol"] == rol and perfil["username"] == usuario, f"Identidad del rol {rol}")
        return token


def inventario(motor):
    """Toma un inventario de las tablas compartidas que ya existen."""
    with motor.connect() as conexion:
        tablas = set(inspect(conexion).get_table_names())
        return {t.name: conexion.scalar(select(func.count()).select_from(t))
                for t in Base.metadata.sorted_tables if t.name in tablas}


def aplicar_migraciones(url_temporal):
    anterior = configuracion.url_base_datos
    configuracion.url_base_datos = url_temporal.render_as_string(hide_password=False)
    try:
        comando = Config(str(RAIZ / "alembic.ini"))
        comando.set_main_option("script_location", str(RAIZ / "alembic"))
        command.upgrade(comando, "head")
    finally:
        configuracion.url_base_datos = anterior


@contextmanager
def servidor_local():
    with socket.socket() as enlace:
        enlace.bind(("127.0.0.1", 0))
        enlace.listen()
        puerto = enlace.getsockname()[1]
        servidor = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
        hilo = Thread(target=servidor.run, kwargs={"sockets": [enlace]}, daemon=True)
        hilo.start()
        try:
            limite = monotonic() + 10
            while hilo.is_alive() and not servidor.started and monotonic() < limite:
                sleep(0.05)
            if not servidor.started:
                raise RuntimeError("No arrancó Bizon API.")
            yield Api(f"http://127.0.0.1:{puerto}")
        finally:
            servidor.should_exit = True
            hilo.join(timeout=10)


def alta_tienda(api, sistema, ruc, nombre, usuario, clave):
    return api.llamar("POST", "/tiendas", 201, token=sistema, datos={
        "ruc": ruc, "razon_social": nombre + " S.A.C.", "nombre_comercial": nombre, "giro": "Bodega",
        "admin_username": usuario, "admin_password": clave,
    })["tienda"]


def alta_cliente(api, admin, documento, nombres, clave, tasa_compensatoria=None):
    return api.llamar("POST", "/clientes", 201, token=admin, datos={
        "tipo_documento": "DNI", "numero_documento": documento, "nombres": nombres, "apellidos": "Validación",
        "password": clave, "condicion": {
            "moneda": "PEN", "limite_credito": "1000.00", "max_meses": 3,
            "dia_corte": 20, "hora_corte": "18:00", "dia_pago": 26, "vigente_desde": "2026-09-01",
            "tasa_compensatoria": tasa_compensatoria or {"tipo": "EFECTIVA", "tasa_pct": "3", "plazo_tasa": 30},
            "tasa_moratoria": {"tipo": "NOMINAL", "tasa_pct": "12", "plazo_tasa": 360, "capitalizacion": 1},
        },
    })


def probar_flujo(api, clave):
    api.llamar("GET", "/tiendas", 401)
    sistema = api.iniciar_sesion(configuracion.admin_sistema_usuario, clave, "ADMIN_SIS")
    rosendo = alta_tienda(api, sistema, "20500000001", "Bodega Don Rosendo", "flujo.rosendo", clave)
    vecina = alta_tienda(api, sistema, "20500000002", "Bodega vecina", "flujo.vecina", clave)
    tiendas = api.llamar("GET", "/tiendas", token=sistema)
    api.comprobar({t["id_tienda"] for t in tiendas} == {rosendo["id_tienda"], vecina["id_tienda"]}, "Tiendas visibles al sistema")
    api.llamar("GET", "/dashboard", 403, token=sistema)

    admin = api.iniciar_sesion("flujo.rosendo", clave, "ADMIN_NEG")
    otro_admin = api.iniciar_sesion("flujo.vecina", clave, "ADMIN_NEG")
    api.llamar("GET", "/tiendas", 403, token=admin)
    mi_tienda = api.llamar("GET", "/mi-tienda", token=admin)
    api.comprobar(mi_tienda["id_tienda"] == rosendo["id_tienda"], "El administrador opera en su tienda")
    unidades = api.llamar("GET", "/unidades-medida", token=admin)
    unidad = next(u for u in unidades if u["codigo"] == "UND")
    marca = api.llamar("POST", "/marcas", 201, token=admin, datos={"nombre": "Buen Campo"})
    proveedor = api.llamar("POST", "/proveedores", 201, token=admin, datos={"razon_social": "Distribuidora de prueba"})
    producto = api.llamar("POST", "/productos", 201, token=admin, datos={
        "codigo": "FLU-01", "nombre": "Canasta familiar", "unidad_id": unidad["id_unidad"],
        "marca_id": marca["id_marca"], "proveedor_id": proveedor["id_proveedor"],
        "precio_contado": "280.00", "precio_lista": "300.00", "permite_cuotas": True, "permite_fin_de_mes": True,
    })
    producto_id = producto["id_producto"]
    api.llamar("GET", f"/productos/{producto_id}", 404, token=otro_admin)
    cliente = alta_cliente(api, admin, "98989801", "Nora", clave)
    ajeno = alta_cliente(api, otro_admin, "98989802", "Pablo", clave)
    cliente_id = cliente["id_cliente"]
    api.llamar("GET", f"/clientes/{cliente_id}", 404, token=otro_admin)

    compra_base = {"cliente_id": cliente_id, "fecha_hora_compra": "2026-09-15T10:00:00",
                   "items": [{"producto_id": producto_id, "cantidad": "1"}]}
    compra_tres_cuotas = {**compra_base, "modalidad": "CUOTAS", "num_cuotas": 3}
    previa = api.llamar("POST", "/compras/simular", token=admin, datos=compra_tres_cuotas)
    api.comprobar(previa["id_compra"] is None and not previa["credito"]["excede_limite"], "Simulación previa sin persistir")
    api.comprobar(previa["dias_gracia"] == 11 and previa["fecha_corte"] == "2026-09-20", "Once días de gracia del enunciado")
    api.comprobar(D(previa["tcea_pct"]) == D("42.5650862"), "TCEA de la simulación con capital original y cuotas redondeadas")
    api.comprobar(D(previa["capital_capitalizado"]) == D("303.27") and D(previa["cuota"]) == D("107.21"), "Capital y cuota francesa")
    cronograma = previa["cronograma"]
    api.comprobar([c["fecha_vencimiento"] for c in cronograma] == ["2026-10-26", "2026-11-26", "2026-12-26"],
                  "Las cuotas comienzan el mes posterior al pago del ciclo")
    api.comprobar([D(c["monto_cuota"]) for c in cronograma] == [D("107.21"), D("107.21"), D("107.22")]
                  and D(cronograma[-1]["saldo_final"]) == 0, "La última cuota absorbe el céntimo de ajuste")
    compra = api.llamar("POST", "/compras", 201, token=admin, datos=compra_tres_cuotas)
    api.comprobar(compra["cronograma"] == cronograma, "El registro conserva el cronograma simulado")
    api.comprobar(compra["tcea_pct"] == previa["tcea_pct"], "La compra registrada conserva la TCEA de la simulación")
    fin_mes = api.llamar("POST", "/compras", 201, token=admin, datos={**compra_base, "modalidad": "FIN_DE_MES"})
    api.comprobar(fin_mes["cronograma"] == [] and D(fin_mes["total_a_pagar"]) == D("303.27"), "Pago único a fin de mes")
    api.comprobar(D(fin_mes["tcea_pct"]) == D("42.5891343"), "TCEA para el pago único a 11 días")
    for operacion, flujos in ((compra, [(41, D("107.21")), (71, D("107.21")), (101, D("107.22"))]),
                              (fin_mes, [(11, D("303.27"))])):
        factor = 1 + D(operacion["tcea_pct"]) / 100
        valor_actual = sum(monto / factor ** (D(dias) / 360) for dias, monto in flujos)
        api.comprobar(abs(valor_actual - D("300.00")) <= D("0.01"), "La TCEA descuenta los flujos al capital original")
    credito = api.llamar("GET", f"/clientes/{cliente_id}/credito-disponible", token=admin)
    api.comprobar(D(credito["credito_disponible"]) == D("396.73"), "Disponible después de las dos compras")

    sept = api.llamar("POST", "/estados-cuenta/generar", token=admin, datos={"anio": 2026, "mes": 9})
    api.comprobar(len(sept) == 1 and sept[0]["fecha_pago"] == "2026-09-26", "Estado del cierre de setiembre")
    repetido = api.llamar("POST", "/estados-cuenta/generar", token=admin, datos={"anio": 2026, "mes": 9})
    api.comprobar(repetido == sept, "Emitir otra vez no duplica el estado de cuenta")
    saldo_sept = f"/estados-cuenta/{sept[0]['id_estado_cuenta']}"
    detalle = api.llamar("GET", saldo_sept, token=admin)
    api.comprobar([linea["tipo_item"] for linea in detalle["detalles"]] == ["COMPRA", "INT_COMPENSATORIO"], "Capital e interés separados")
    api.llamar("GET", saldo_sept, 404, token=otro_admin)
    octu = api.llamar("POST", "/estados-cuenta/generar", token=admin, datos={"anio": 2026, "mes": 10})
    api.comprobar(len(octu) == 1 and D(octu[0]["total_pagar"]) == D("107.21"), "En octubre se emite la primera cuota")
    api.llamar("POST", f"/clientes/{cliente_id}/baja", 409, token=admin)

    pago_sept = "/pagos" + saldo_sept
    exigible = api.llamar("GET", pago_sept + "/exigible?fecha_pago=2026-10-02", token=admin)
    api.comprobar(exigible["dias_mora"] == 6 and D(exigible["tasa_mora_pct"]) == D("0.2001667"), "Mora comercial y tasa efectiva del atraso")
    api.comprobar(D(exigible["interes_mora"]) == D("0.61") and D(exigible["interes_comp_atraso"]) == D("1.80"),
                  "Mora y compensatorio adicional del caso")
    api.comprobar(D(exigible["total_exigible"]) == D("305.68"), "Total exigible del 2 de octubre")
    api.llamar("GET", pago_sept + "/exigible", 404, token=otro_admin)
    api.llamar("POST", pago_sept, 400, token=admin, datos={"monto_pagado": "1.00", "fecha_pago": "2026-10-02"})
    impago = api.llamar("GET", saldo_sept, token=admin)
    api.comprobar(impago["estado"] == "VENCIDO" and len(impago["detalles"]) == 2, "El pago parcial deja intacto el estado")
    pago = api.llamar("POST", pago_sept, 201, token=admin, datos={"monto_pagado": "315.68", "fecha_pago": "2026-10-02"})
    api.comprobar(D(pago["excedente_devuelto"]) == D("10.00") and pago["estado_cuenta"] == "PAGADO", "Excedente y pago confirmado")
    api.llamar("POST", pago_sept, 409, token=admin, datos={"monto_pagado": "315.68", "fecha_pago": "2026-10-02"})
    cancelada = api.llamar("GET", f"/compras/{fin_mes['id_compra']}", token=admin)
    api.comprobar(cancelada["estado"] == "CANCELADA", "La compra a fin de mes queda cancelada")
    api.comprobar(cancelada["tcea_pct"] == fin_mes["tcea_pct"], "La mora cobrada no altera la TCEA programada")
    api.llamar("POST", f"/pagos/estados-cuenta/{octu[0]['id_estado_cuenta']}", 201, token=admin,
              datos={"monto_pagado": "107.21", "fecha_pago": "2026-10-26"})

    titular = api.iniciar_sesion(cliente["usuario"], clave, "CLIENTE")
    otro_cliente = api.iniciar_sesion(ajeno["usuario"], clave, "CLIENTE")
    api.llamar("GET", "/dashboard", 403, token=titular)
    api.llamar("GET", "/mi-cuenta/resumen", 403, token=admin)
    api.llamar("GET", "/mi-cuenta" + saldo_sept, 404, token=otro_cliente)
    estados = api.llamar("GET", "/mi-cuenta/estados-cuenta", token=titular)
    api.comprobar(len(estados) == 2 and all(e["cliente_id"] == cliente_id and e["estado"] == "PAGADO" for e in estados),
                  "El titular ve sus estados pagados")
    pagado = api.llamar("GET", "/mi-cuenta" + saldo_sept, token=titular)
    mora = next(linea for linea in pagado["detalles"] if linea["tipo_item"] == "INT_MORATORIO")
    api.comprobar(mora["concepto"] == "Intereses por mora" and mora["dias_transcurridos"] == 6 and D(mora["monto"]) == D("0.61"),
                  "La mora queda como ítem con días y monto en el estado original")
    api.comprobar(D(pagado["total_pagar"]) == sum(D(f["monto"]) for f in pagado["detalles"]), "El detalle pagado cuadra con el total")
    compras = api.llamar("GET", "/mi-cuenta/compras", token=titular)
    api.comprobar({c["id_compra"]: c["tcea_pct"] for c in compras} == {
        compra["id_compra"]: compra["tcea_pct"], fin_mes["id_compra"]: fin_mes["tcea_pct"],
    }, "El titular ve la TCEA de las dos compras")
    cuotas_guardadas = next(c["cronograma"] for c in compras if c["modalidad"] == "CUOTAS")
    api.comprobar(len(compras) == 2 and [q["estado"] for q in cuotas_guardadas] == ["PAGADA", "PENDIENTE", "PENDIENTE"],
                  "El pago de octubre no adelanta cuotas futuras")
    resumen = api.llamar("GET", "/mi-cuenta/resumen", token=titular)
    api.comprobar(D(resumen["posicion"]["saldo_capital"]) == D("205.16"), "Saldo de capital después del primer pago")
    tablero = api.llamar("GET", "/dashboard", token=admin)
    api.comprobar(D(tablero["kpis"]["saldo_por_cobrar"]) == D("205.16"), "El tablero concilia con la cuenta del cliente")

    nominal = alta_cliente(api, admin, "98989803", "Teresa", clave, {
        "tipo": "NOMINAL", "tasa_pct": "36", "plazo_tasa": 360, "capitalizacion": 30,
    })
    for modalidad, efectiva in ((compra_tres_cuotas, compra), ({**compra_base, "modalidad": "FIN_DE_MES"}, fin_mes)):
        simulada_nominal = api.llamar("POST", "/compras/simular", token=admin, datos={**modalidad, "cliente_id": nominal["id_cliente"]})
        api.comprobar(simulada_nominal["tcea_pct"] == efectiva["tcea_pct"], "TNA 36 % capitalizada al mes y TEM 3 % equivalentes")


def probar_calculadora_tcea(api):
    ruta = "/finanzas/tcea"
    pagos = [{"monto": "1030.00", "dias": 30}, {"monto": "2121.80", "dias": 60}, {"monto": "10927.27", "dias": 90}]
    normal = api.llamar("POST", ruta, datos={"monto_recibido": "13000.00", "pagos": pagos})
    tea = (D("1.03") ** 12 - 1) * 100
    api.comprobar(abs(D(normal["tcea_pct"]) - tea) < D("0.0000001"), "Sin redondeo de los flujos, la TCEA coincide con la TEA")
    escala = D("3.47")
    originales = [
        {"monto": "1030.00", "dias": 30}, {"monto": "2121.00", "dias": 60}, {"monto": "10927.00", "dias": 90},
    ]
    convertidos = [{**p, "monto": format(D(p["monto"]) * escala, ".2f")} for p in originales]
    pen = api.llamar("POST", ruta, datos={"monto_recibido": "45110.00", "pagos": convertidos})
    usd = api.llamar("POST", ruta, datos={"monto_recibido": "13000.00", "pagos": originales})
    api.comprobar(pen == usd, "Expresar el mismo flujo en PEN o USD no cambia su tasa")

    mas_caros = [{**p, "monto": str(D(p["monto"]) + 1)} for p in pagos]
    mayor = api.llamar("POST", ruta, datos={"monto_recibido": "13000.00", "pagos": mas_caros})
    api.comprobar(D(mayor["tcea_pct"]) > D(normal["tcea_pct"]), "Cuotas más caras en las mismas fechas elevan la TCEA")
    mas_tarde = [{**p, "dias": p["dias"] + 11} for p in pagos]
    menor = api.llamar("POST", ruta, datos={"monto_recibido": "13000.00", "pagos": mas_tarde})
    api.comprobar(D(menor["tcea_pct"]) < D(normal["tcea_pct"]), "Aplazar los mismos importes reduce la tasa anual")

    cero = api.llamar("POST", ruta, datos={"monto_recibido": "100.00", "pagos": [{"monto": "100.00", "dias": 30}]})
    api.comprobar(cero["tcea_pct"] == "0.0000000", "TCEA nula serializada con siete decimales")
    negativa = api.llamar("POST", ruta, datos={"monto_recibido": "100.00", "pagos": [{"monto": "40.00", "dias": 30}, {"monto": "50.00", "dias": 60}]})
    api.comprobar(-100 < D(negativa["tcea_pct"]) < 0, "La bisección admite flujos que devuelven menos que el capital")
    api.llamar("POST", ruta, 422, datos={"monto_recibido": "100.00", "pagos": [{"monto": "0.00", "dias": 30}]})
    api.llamar("POST", ruta, 422, datos={"monto_recibido": "100.00", "fecha_compra": "2026-01-30",
               "pagos": [{"monto": "103.00", "fecha": "2026-01-31"}]})


def main():
    esquema = "bizon_flujo_" + uuid4().hex
    url = make_url(configuracion.url_base_datos)
    compartido = create_engine(url)
    temporal = create_engine(url.update_query_dict({"options": f"-csearch_path={esquema}"}))
    antes = inventario(compartido)
    with compartido.begin() as conexion:
        conexion.execute(CreateSchema(esquema))
    try:
        aplicar_migraciones(temporal.url)
        SesionLocal.configure(bind=temporal)
        clave = uuid4().hex
        configuracion.admin_sistema_usuario = "flujo.sistema"
        configuracion.admin_sistema_password = clave
        cargar_seeds()
        with servidor_local() as api:
            probar_flujo(api, clave)
            probar_calculadora_tcea(api)
    finally:
        temporal.dispose()
        with compartido.begin() as conexion:
            conexion.execute(DropSchema(esquema, cascade=True))
        try:
            if inspect(compartido).has_schema(esquema) or inventario(compartido) != antes:
                raise AssertionError("La base compartida debe conservar el inventario original.")
        finally:
            compartido.dispose()
    print(f"RESULTADO: {api.comprobaciones} comprobaciones HTTP y limpieza verificada.")


if __name__ == "__main__":
    main()
