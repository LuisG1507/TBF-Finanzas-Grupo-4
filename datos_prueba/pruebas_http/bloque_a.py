"""Prueba el bloque A por HTTP real y limpia el esquema PostgreSQL temporal al terminar.

Ejecutar desde Backend-Grupo4: python -m datos_prueba.pruebas_http.bloque_a
"""
import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from threading import Thread
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import uvicorn
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema

from app.core.configuracion import configuracion
from app.core.tiempo import ZONA_LIMA
from app.db.base import Base
from app.db.demo import CLAVE_DEMO, operar_demo
from app.db.seeds import cargar_seeds
from app.db.sesion import SesionLocal
from app.main import app
from app.models import Bitacora, Cliente, Compra, EstadoCuenta, Pago, Producto, Tienda, Usuario
from app.models.enumeraciones import EntidadBitacora
from app.services import servicio_estados_cuenta, servicio_resumen

sys.stdout.reconfigure(errors="backslashreplace")
esquema = "codex_prueba_ec_" + uuid4().hex
control = create_engine(configuracion.url_base_datos)
motor_pruebas = None
checks = 0

def comprobar(valor, razon):
    global checks
    assert valor, razon
    checks += 1

def conteos_publicos():
    with control.connect() as conn:
        return tuple(conn.scalar(select(func.count()).select_from(m)) for m in (Tienda, Usuario, Cliente, Compra, EstadoCuenta, Pago))

def llamar(metodo, ruta, *, datos=None, token=None, esperado=200, formulario=False):
    headers = {}
    cuerpo = None
    if datos is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded" if formulario else "application/json"
        cuerpo = (urlencode(datos) if formulario else json.dumps(datos)).encode()
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url_base + ruta, data=cuerpo, method=metodo, headers=headers)
    try:
        with urlopen(req, timeout=10) as resp:
            codigo, respuesta = resp.status, resp.read()
    except HTTPError as resp:
        codigo, respuesta = resp.code, resp.read()
    contenido = json.loads(respuesta) if respuesta else None
    comprobar(codigo == esperado, f"{metodo} {ruta}: esperaba {esperado}, recibí {codigo} {contenido}")
    return contenido

def login(nombre, password=None):
    return llamar("POST", "/auth/login", datos={"username": nombre, "password": password or clave}, formulario=True)["access_token"]

def crear_tienda(token, nombre, ruc, comercial=None):
    return llamar("POST", "/tiendas", token=token, esperado=201, datos={
        "ruc": ruc, "giro": "bodega", "razon_social": nombre, "nombre_comercial": comercial or nombre,
        "admin_username": nombre, "admin_password": clave,
    })

def crear_cliente(token, numero, condicion_credito):
    cliente = llamar("POST", "/clientes", token=token, esperado=201, datos={
        "tipo_documento": "DNI", "numero_documento": numero, "nombres": "Cliente", "apellidos": "Prueba",
        "password": clave, "condicion": condicion_credito,
    })
    return cliente["id_cliente"]

def generar(mes, token):
    return llamar("POST", "/estados-cuenta/generar", datos={"anio": 2026, "mes": mes}, token=token)

def comprar(dia, modalidad="FIN_DE_MES", *, esperado=201, ruta="/compras", comprador=None):
    datos = {"cliente_id": comprador or cliente, "modalidad": modalidad, "items": [{"producto_id": producto, "cantidad": "3"}], "fecha_hora_compra": dia}
    if modalidad == "CUOTAS":
        datos["num_cuotas"] = 3
    return llamar("POST", ruta, token=admin, datos=datos, esperado=esperado)

def reloj(momento):
    fecha = datetime.fromisoformat(momento).replace(tzinfo=ZONA_LIMA)
    servicio_estados_cuenta.ahora_lima = lambda: fecha
    servicio_estados_cuenta.hoy_lima = lambda: fecha.date()

antes = conteos_publicos()
with control.begin() as conexion:
    conexion.execute(CreateSchema(esquema))
try:
    motor_pruebas = create_engine(configuracion.url_base_datos, connect_args={"options": f"-csearch_path={esquema}"})
    Base.metadata.create_all(motor_pruebas)
    SesionLocal.configure(bind=motor_pruebas)
    clave = uuid4().hex
    configuracion.admin_sistema_usuario = "verificacion.ec"
    configuracion.admin_sistema_password = clave
    cargar_seeds()

    with socket.socket() as enlace:
        enlace.bind(("127.0.0.1", 0))
        enlace.listen()
        url_base = f"http://127.0.0.1:{enlace.getsockname()[1]}/api/v1"
        servidor = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
        hilo = Thread(target=servidor.run, kwargs={"sockets": [enlace]}, daemon=True)
        hilo.start()
        try:
            limite = monotonic() + 10
            while not servidor.started and hilo.is_alive() and monotonic() < limite:
                sleep(0.05)
            assert servidor.started
            sis = login(configuracion.admin_sistema_usuario)
            crear_tienda(sis, "tienda.prueba.1", "20500000001", "Bodega Don Rosendo")
            crear_tienda(sis, "tienda.prueba.2", "20500000002")
            admin = login("tienda.prueba.1")
            otra_tienda = login("tienda.prueba.2")
            condicion = {
                "moneda": "PEN", "tasa_compensatoria": {"tipo": "EFECTIVA", "tasa_pct": "3", "plazo_tasa": "MENSUAL"},
                "tasa_moratoria": {"tipo": "NOMINAL", "tasa_pct": "12", "plazo_tasa": "ANUAL", "capitalizacion": "DIARIA"},
                "limite_credito": "10000", "max_meses": 6, "dia_corte": 20, "dia_pago": 26,
                "hora_corte": "18:00", "vigente_desde": "2026-08-01",
            }
            cliente = crear_cliente(admin, "99000001", condicion)
            sin_deuda = crear_cliente(admin, "99000002", condicion)
            cliente_otra_tienda = crear_cliente(otra_tienda, "99000003", condicion)
            titular, ajeno, externo = [login(n) for n in ("99000001", "99000002", "99000003")]
            unidad = llamar("GET", "/unidades-medida", token=admin)[0]["id_unidad"]
            producto = llamar("POST", "/productos", token=admin, esperado=201, datos={
                "codigo": "EC01", "nombre": "Unidad prueba", "descripcion": "Para prueba",
                "unidad_id": unidad, "precio_contado": "90", "precio_lista": "100",
                "permite_fin_de_mes": True, "permite_cuotas": True,
            })["id_producto"]

            cuotas = comprar("2026-09-15T10:00:00", "CUOTAS")
            fin_tarde = comprar("2026-09-18T14:00:00")
            fin_antes = comprar("2026-09-15T09:00:00")
            fin_en_corte = comprar("2026-09-20T18:00:00")
            comprobar(cuotas["dias_gracia"] == 11, "11 días de gracia")
            comprobar(Decimal(cuotas["tcea_pct"]) == Decimal("42.5650862"), "TCEA de las tres cuotas redondeadas del 15-set")
            comprobar(Decimal(fin_antes["tcea_pct"]) == Decimal("42.5891343"), "TCEA del pago único redondeado del 15-set")
            comprobar([c["fecha_vencimiento"] for c in cuotas["cronograma"]] ==
                      ["2026-10-26", "2026-11-26", "2026-12-26"], "vencimientos del enunciado")
            comprobar(fin_en_corte["fecha_corte"] == "2026-10-20", "compra en corte pasa al mes siguiente")

            reloj("2026-09-20T17:59:59")
            comprobar(generar(9, admin) == [], "una fracción antes del corte")
            llamar("POST", "/estados-cuenta/generar", datos={"anio": 2026, "mes": 10}, token=admin, esperado=422)
            llamar("POST", "/estados-cuenta/generar", datos={"anio": 2026, "mes": 9}, token=titular, esperado=403)
            llamar("POST", "/estados-cuenta/generar", datos={"anio": 2026, "mes": 9}, esperado=401)
            reloj("2026-09-20T18:00:00")
            with ThreadPoolExecutor(max_workers=2) as pool:
                a, b = list(pool.map(lambda _: generar(9, admin), range(2)))
            comprobar(len(a) == 1 and a == b, "emisión concurrente sin duplicados")
            sep = a[0]
            sid = sep["id_estado_cuenta"]
            comprobar(sep["estado"] == "EMITIDO" and sep["fecha_pago"] == "2026-09-26", "vencimiento ordinario")
            comprobar(sep["moneda"]["codigo_iso"] == "PEN", "moneda obtenida de la compra")
            detalle = llamar("GET", f"/estados-cuenta/{sid}", token=admin)["detalles"]
            comprobar([d["tipo_item"] for d in detalle] == ["COMPRA", "INT_COMPENSATORIO"] * 2, "únicamente obligaciones de fin de mes")
            ids = [fin_antes["id_compra"], fin_tarde["id_compra"]]
            comprobar([d["compra_id"] for d in detalle] == [ids[0], ids[0], ids[1], ids[1]], "orden por fecha de compra")
            comprobar([d["orden"] for d in detalle] == [1, 2, 3, 4], "orden de ítems")
            comprobar([d["dias_transcurridos"] for d in detalle if d["tipo_item"] == "INT_COMPENSATORIO"] == [11, 8], "días de compra a pago")
            comprobar(Decimal(detalle[1]["tasa_aplicada"]) == Decimal(fin_antes["tep_aplicada"]), "TEP original")
            comprobar(Decimal(sep["total_interes_comp"]) == sum(Decimal(f["interes_gracia"]) for f in (fin_antes, fin_tarde)), "usa el interés persistido")
            comprobar(Decimal(sep["total_pagar"]) == sum(Decimal(d["monto"]) for d in detalle), "detalle cuadra con el total")
            comprobar(generar(9, otra_tienda) == [], "emisión aislada por tienda")
            llamar("GET", f"/estados-cuenta/{sid}", token=otra_tienda, esperado=404)
            llamar("GET", f"/estados-cuenta/{sid}", token=titular, esperado=403)
            llamar("GET", f"/mi-cuenta/estados-cuenta/{sid}", token=ajeno, esperado=404)
            llamar("GET", f"/mi-cuenta/estados-cuenta/{sid}", token=externo, esperado=404)
            llamar("GET", f"/mi-cuenta/estados-cuenta/{sid}", token=titular)
            comprobar(len(llamar("GET", "/mi-cuenta/estados-cuenta", token=titular)) == 1, "cliente consulta su historial")
            comprobar(llamar("GET", "/mi-cuenta/estados-cuenta", token=ajeno) == [], "cliente sin estados")
            comprobar(llamar("GET", f"/estados-cuenta?cliente_id={cliente_otra_tienda}", token=admin) == [], "filtro por cliente no cruza tiendas")
            llamar("GET", "/estados-cuenta", token=sis, esperado=403)

            comprar("2026-09-19T14:00:00", esperado=409)
            comprar("2026-09-19T14:00:00", esperado=409, ruta="/compras/simular")
            comprar("2026-08-15T10:00:00", "CUOTAS", esperado=409)
            llamar("POST", f"/compras/{ids[0]}/anular", token=admin, datos={"motivo": "Prueba de corte"}, esperado=409)
            cond_usd = {**condicion, "moneda": "USD", "vigente_desde": "2026-09-21"}
            llamar("PUT", f"/clientes/{cliente}/condicion", token=admin, datos=cond_usd, esperado=409)
            llamar("PUT", f"/clientes/{sin_deuda}/condicion", token=admin, datos=cond_usd)
            llamar("PUT", f"/clientes/{cliente}/condicion", token=admin, datos={
                **condicion, "dia_pago": 10, "vigente_desde": "2026-09-21",
            })
            nuevo_pacto = comprar("2026-10-10T12:00:00")

            reloj("2026-09-26T23:59:59")
            comprobar(llamar("GET", "/estados-cuenta?estado=VENCIDO", token=admin) == [], "vence después del día de pago")
            reloj("2026-10-20T18:00:00")
            octs = generar(10, admin)
            comprobar([e["fecha_pago"] for e in octs] == ["2026-10-26", "2026-11-10"], "dos vencimientos bajo pactos distintos")
            fila = llamar("GET", f"/estados-cuenta/{octs[0]['id_estado_cuenta']}", token=admin)["detalles"][0]
            comprobar(fila["tipo_item"] == "CUOTA" and fila["numero_cuota"] == 1, "entra solo la cuota de octubre")
            comprobar(fila["compra_id"] == cuotas["id_compra"] and fila["cuota_id"] is not None, "vínculo a cuota y compra")
            primera = cuotas["cronograma"][0]
            comprobar(Decimal(fila["monto"]) == Decimal(primera["monto_cuota"]) and
                      Decimal(fila["amortizacion"]) == Decimal(primera["amortizacion"]) and
                      Decimal(fila["interes_cuota"]) == Decimal(primera["interes"]), "cronograma original intacto")
            otra = llamar("GET", f"/estados-cuenta/{octs[1]['id_estado_cuenta']}", token=admin)["detalles"][0]
            comprobar(otra["compra_id"] == nuevo_pacto["id_compra"], "pacto de pago del mes siguiente")
            vencidos = llamar("GET", "/estados-cuenta?estado=VENCIDO", token=admin)
            comprobar([v["id_estado_cuenta"] for v in vencidos] == [sid], "filtro de vencimiento derivado")
            activos = llamar("GET", "/estados-cuenta?estado=EMITIDO&anio=2026&mes=10&limite=1", token=admin)
            comprobar(len(activos) == 1, "filtros de estado, periodo y paginación")
            compra_db = llamar("GET", f"/compras/{cuotas['id_compra']}", token=admin)
            comprobar([f["estado"] for f in compra_db["cronograma"]] == ["FACTURADA", "PENDIENTE", "PENDIENTE"], "solo la cuota del corte queda facturada")
            antigua_rechazada = comprar("2026-09-20T18:00:00", comprador=sin_deuda, esperado=409)
            comprobar("moneda anterior (PEN)" in antigua_rechazada["detail"], "motivo del rechazo de operación retroactiva")
            comprar("2026-09-20T18:00:00", comprador=sin_deuda, esperado=409, ruta="/compras/simular")
            antigua = comprar("2026-10-11T11:00:00", comprador=sin_deuda)
            vigente = comprar("2026-10-10T12:00:00", comprador=sin_deuda)
            with SesionLocal.begin() as session:
                from app.models.cliente import CondicionCredito
                anterior = session.scalar(select(CondicionCredito).where(
                    CondicionCredito.cliente_id == sin_deuda, CondicionCredito.vigente_hasta.is_not(None)
                ))
                session.get(Compra, antigua["id_compra"]).condicion_id = anterior.id_condicion
            conflicto = llamar("POST", "/estados-cuenta/generar", datos={"anio": 2026, "mes": 10}, token=admin, esperado=409)
            comprobar("monedas distintas" in conflicto["detail"], "el generador rechaza monedas mezcladas")
            for conflictiva in (antigua, vigente):
                llamar("POST", f"/compras/{conflictiva['id_compra']}/anular", token=admin, datos={"motivo": "Retirar dato de prueba"})
            comprobar(generar(10, admin) == octs, "reintento después de resolver la inconsistencia")
            with SesionLocal() as session:
                bitacora = list(session.scalars(select(Bitacora).where(Bitacora.entidad == EntidadBitacora.ESTADO_CUENTA)))
                comprobar(len(bitacora) == 3, "un alta por estado y sin duplicar bitácora")
                comprobar({x.entidad_id for x in bitacora} == {sid, *(e["id_estado_cuenta"] for e in octs)}, "auditoría vinculada a estados emitidos")

            llamar("POST", f"/clientes/{cliente}/baja", token=admin, esperado=409)
            llamar("POST", f"/clientes/{cliente}/baja", token=otra_tienda, esperado=404)
            fecha_pago_sep = "2026-10-02"
            pagos_ruta = f"/pagos/estados-cuenta/{sid}"
            llamar("GET", f"{pagos_ruta}/exigible", token=otra_tienda, esperado=404)
            llamar("GET", f"{pagos_ruta}/exigible", token=titular, esperado=403)
            exigible = llamar("GET", f"{pagos_ruta}/exigible?fecha_pago={fecha_pago_sep}", token=admin)
            comprobar(exigible["dias_mora"] == 6, "seis días comerciales de atraso")
            comprobar(Decimal(exigible["interes_mora"]) == Decimal("1.21"), "mora del caso de setiembre")
            comprobar(Decimal(exigible["interes_comp_atraso"]) == Decimal("3.59"), "compensatorio del atraso")
            comprobar(Decimal(exigible["total_exigible"]) == Decimal("610.44"), "total exigible del caso")
            llamar("POST", pagos_ruta, token=admin, datos={"fecha_pago": fecha_pago_sep, "monto_pagado": "0.01"}, esperado=400)
            sin_pagar = llamar("GET", f"/estados-cuenta/{sid}", token=admin)
            comprobar(len(sin_pagar["detalles"]) == 4 and sin_pagar["estado"] != "PAGADO", "el pago parcial no altera el estado")
            pago_sep = llamar("POST", pagos_ruta, token=admin, esperado=201,
                              datos={"fecha_pago": fecha_pago_sep, "monto_pagado": "620.44"})
            comprobar(pago_sep["estado_cuenta"] == "PAGADO" and Decimal(pago_sep["excedente_devuelto"]) == Decimal(10),
                      "el pago tardío cancela el estado y devuelve el excedente")
            llamar("POST", pagos_ruta, token=admin, datos={"fecha_pago": fecha_pago_sep, "monto_pagado": "620.44"}, esperado=409)
            llamar("GET", f"{pagos_ruta}/exigible", token=admin, esperado=409)
            pagado = llamar("GET", f"/estados-cuenta/{sid}", token=admin)
            mora, compensatorio = pagado["detalles"][-2:]
            comprobar(pagado["estado"] == "PAGADO" and Decimal(pagado["total_interes_mora"]) == Decimal("1.21"),
                      "consulta refleja pago y mora")
            comprobar(mora["tipo_item"] == "INT_MORATORIO" and mora["concepto"] == "Intereses por mora", "ítem separado")
            comprobar(mora["dias_transcurridos"] == 6 and mora["fecha_referencia"] == fecha_pago_sep, "detalle del atraso")
            comprobar(Decimal(mora["tasa_aplicada"]) == Decimal("0.2001667") and Decimal(mora["monto"]) == Decimal("1.21"),
                      "tasa efectiva de mora con siete decimales y monto")
            comprobar(compensatorio["concepto"] == "Intereses compensatorios por atraso" and Decimal(compensatorio["monto"]) == Decimal("3.59"),
                      "desglose del compensatorio de atraso")
            comprobar(Decimal(pagado["total_pagar"]) == sum(Decimal(d["monto"]) for d in pagado["detalles"]),
                      "los detalles y totales pagados cuadran")
            for compra_id in ids:
                comprobar(llamar("GET", f"/compras/{compra_id}", token=admin)["estado"] == "CANCELADA", "pago cancela la compra a fin de mes")

            primer_estado = octs[0]
            ruta_oct = f"/pagos/estados-cuenta/{primer_estado['id_estado_cuenta']}"
            pagar_octubre = llamar("POST", ruta_oct, token=admin, esperado=201,
                                   datos={"fecha_pago": primer_estado["fecha_pago"], "monto_pagado": primer_estado["total_pagar"]})
            comprobar(pagar_octubre["estado_cuenta"] == "PAGADO" and Decimal(pagar_octubre["interes_mora"]) == 0, "pago puntual de cuota")
            compra_pagada = llamar("GET", f"/compras/{cuotas['id_compra']}", token=admin)
            comprobar([f["estado"] for f in compra_pagada["cronograma"]] == ["PAGADA", "PENDIENTE", "PENDIENTE"],
                      "el pago solo cancela la primera cuota")
            baja = llamar("POST", f"/clientes/{sin_deuda}/baja", token=admin)
            comprobar(baja["activo"] is False, "el cliente sin deuda puede darse de baja")
            llamar("GET", "/mi-cuenta/resumen", token=ajeno, esperado=403)

            reloj("2026-11-25T12:00:00")
            servicio_resumen.hoy_lima = lambda: datetime(2026, 11, 25).date()
            id_usd = crear_cliente(admin, "99000004", cond_usd)
            comprar("2026-11-10T12:00:00", comprador=id_usd)
            generar(11, admin)
            tablero = llamar("GET", "/dashboard", token=admin)
            comprobar(tablero["moneda_base"] == "PEN" and tablero["hoy"] == "2026-11-25", "cabecera del tablero")
            comprobar(len(tablero["cobranza_semanal"]) == 8 and len(tablero["cierres_mensuales"]) == 5, "periodos de los reportes")
            cierre_sep = next(cierre for cierre in tablero["cierres_mensuales"] if cierre["mes"] == "2026-09-01")
            comprobar(Decimal(cierre_sep["mora_acumulada"]) == Decimal("0.81"), "mora al cierre, antes del pago de octubre")
            comprobar(tablero["kpis"]["clientes_activos"] == 2, "conteo de clientes activos de la tienda")
            pos = {p["cliente_id"]: p for p in tablero["posiciones"]}
            comprobar(Decimal(pos[cliente]["saldos_cierre_previos"][-2]) == Decimal("900.00") + Decimal(cuotas["capital_capitalizado"]),
                      "capital histórico al cierre de setiembre")
            comprobar(pos[cliente]["situacion"] == "EN_MORA" and pos[cliente]["proximo_vencimiento"] == "2026-11-10",
                      "situación de mora y vencimiento más antiguo")
            exigible_nov = llamar("GET", f"/pagos/estados-cuenta/{octs[1]['id_estado_cuenta']}/exigible?fecha_pago=2026-11-25", token=admin)
            comprobar(Decimal(pos[cliente]["mora_acumulada"]) == Decimal(exigible_nov["interes_mora"]), "tablero y pago calculan la misma mora")
            comprobar(pos[id_usd]["moneda"] == "USD" and pos[id_usd]["situacion"] == "POR_VENCER", "posición en dólares próxima a vencer")
            saldo_esperado = Decimal(pos[cliente]["saldo_capital"]) + (Decimal(pos[id_usd]["saldo_capital"]) * Decimal("3.47")).quantize(Decimal(".01"))
            comprobar(Decimal(tablero["kpis"]["saldo_por_cobrar"]) == saldo_esperado, "capital consolidado en soles")
            comprobar(Decimal(tablero["kpis"]["cuotas_del_mes"]) ==
                      sum(Decimal(q["monto"]) for q in tablero["cuotas_del_mes"]), "cuotas del mes consolidadas")
            comprobar(sum(Decimal(s["cobrado"]) for s in tablero["cobranza_semanal"]) == Decimal(primer_estado["total_pagar"]),
                      "cobranza semanal usa fecha y valor pagados")
            tablero_ajeno = llamar("GET", "/dashboard", token=otra_tienda)
            comprobar(Decimal(tablero_ajeno["kpis"]["saldo_por_cobrar"]) == 0, "tablero aislado por tienda")
            llamar("GET", "/dashboard", token=titular, esperado=403)
            llamar("GET", "/dashboard", token=sis, esperado=403)
            llamar("GET", "/mi-cuenta/resumen", token=admin, esperado=403)
            llamar("GET", "/mi-cuenta/compras", esperado=401)
            propia = llamar("GET", "/mi-cuenta/resumen", token=titular)
            comprobar(propia["posicion"] == pos[cliente] and propia["tienda"] == "Bodega Don Rosendo", "resumen de cuenta del titular")
            mis_compras = llamar("GET", f"/mi-cuenta/compras?cliente_id={id_usd}", token=titular)
            comprobar(len(mis_compras) > 0 and all(p["cliente"]["id_cliente"] == cliente for p in mis_compras),
                      "el historial solo devuelve compras del usuario autenticado")
            comprobar(any(len(c["cronograma"]) == 3 for c in mis_compras), "las compras propias incluyen cronograma")

            comprobar("9 clientes, 6 productos, 18 compras" in operar_demo(motor_db=motor_pruebas), "carga inicial de la demo")
            comprobar("ya están cargados" in operar_demo(motor_db=motor_pruebas), "demo idempotente")
            demo_usd = login("demo.elena", CLAVE_DEMO)
            demo_mi_cuenta = llamar("GET", "/mi-cuenta/resumen", token=demo_usd)
            comprobar(demo_mi_cuenta["posicion"]["moneda"] == "USD", "cliente demo en dólares")
            demo_tardio = login("demo.jorge", CLAVE_DEMO)
            estados_demo = llamar("GET", "/mi-cuenta/estados-cuenta", token=demo_tardio)
            tardio = next(e for e in estados_demo if e["mes"] == 9)
            comprobar(tardio["estado"] == "PAGADO" and Decimal(tardio["total_interes_mora"]) > 0, "la demo trae pago tardío")
            demo_rosa = login("demo.rosa", CLAVE_DEMO)
            comprobar(llamar("GET", "/mi-cuenta/resumen", token=demo_rosa)["posicion"]["situacion"] == "EN_MORA",
                      "la demo trae un estado vencido")
            comprobar("retirados" in operar_demo(limpiar=True, motor_db=motor_pruebas), "limpieza de la demo")
            comprobar("no tiene datos" in operar_demo(limpiar=True, motor_db=motor_pruebas), "limpieza idempotente")
            comprobar(llamar("GET", "/dashboard", token=admin) == tablero, "la limpieza deja intactos los datos ajenos a la demo")
            llamar("GET", "/mi-cuenta/resumen", token=demo_usd, esperado=401)
            operar_demo(motor_db=motor_pruebas)
            with SesionLocal() as session:
                producto_demo = session.scalar(select(Producto.id_producto).where(Producto.codigo == "DEMO-ARR"))
            llamar("POST", "/compras", token=admin, esperado=201, datos={
                "cliente_id": cliente, "modalidad": "FIN_DE_MES", "fecha_hora_compra": "2026-11-24T10:00:00",
                "items": [{"producto_id": producto_demo, "cantidad": "1"}],
            })
            try:
                operar_demo(limpiar=True, motor_db=motor_pruebas)
            except IntegrityError:
                comprobar("ya están cargados" in operar_demo(motor_db=motor_pruebas), "la limpieza revierte ante referencias ajenas")
            else:
                comprobar(False, "la limpieza debe preservar compras ajenas a la demo")
            from contextlib import redirect_stdout
            from io import StringIO
            sys.path.insert(0, "datos_prueba")
            from verificar_casos import main
            sys.argv = ["verificar_casos.py", "--url", url_base]
            resultado_curso = StringIO()
            with redirect_stdout(resultado_curso):
                codigo_curso = main()
            comprobar(codigo_curso == 0, resultado_curso.getvalue())
            print(resultado_curso.getvalue().strip().splitlines()[-1])
        finally:
            servidor.should_exit = True
            hilo.join(timeout=8)
finally:
    if motor_pruebas is not None:
        motor_pruebas.dispose()
    with control.begin() as conexion:
        conexion.execute(DropSchema(esquema, cascade=True))
    comprobar(conteos_publicos() == antes, "la base compartida quedó intacta")

print(f"RESULTADO: {checks} comprobaciones correctas con HTTP real y PostgreSQL.")
