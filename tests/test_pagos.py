"""Pruebas del endpoint de pagos con los datos del Ejercicio 2 del informe.
Usan SQLite en memoria, asi que no necesitan Postgres: python -m pytest tests"""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models as m
from app.db.base import Base
from app.db.sesion import obtener_sesion
from app.main import app
from app.models.enumeraciones import (
    EstadoCompra,
    EstadoCuota,
    ModalidadCompra,
    RolCodigo,
    TipoItemEstadoCuenta,
    TipoTasa,
)

URL = "/api/v1/pagos/estados-cuenta"
D = Decimal


@pytest.fixture
def entorno():
    motor = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(motor)
    Sesion = sessionmaker(bind=motor, autoflush=False)
    s = Sesion()

    tienda = m.Tienda(ruc="20123456789", razon_social="Bodega SAC", nombre_comercial="Bodega", giro="Bodega")
    rol = m.Rol(codigo=RolCodigo.ADMIN_NEG, nombre="Administrador del negocio")
    moneda = m.Moneda(codigo_iso="PEN", nombre="Sol", simbolo="S/")
    s.add_all([tienda, rol, moneda])
    s.flush()
    admin = m.Usuario(rol_id=rol.id_rol, tienda_id=tienda.id_tienda, username="admin", password_hash="x")
    usuario_cliente = m.Usuario(rol_id=rol.id_rol, tienda_id=tienda.id_tienda, username="cliente", password_hash="x")
    s.add_all([admin, usuario_cliente])
    s.flush()
    cliente = m.Cliente(tienda_id=tienda.id_tienda, usuario_id=usuario_cliente.id_usuario, tipo_documento="DNI",
                        numero_documento="12345678", nombres="Ana", apellidos="Perez")
    s.add(cliente)
    s.flush()
    # Ejercicio 2: TNA compensatoria 24% cap. mensual; TNA moratoria 12% cap. diaria; corte 20, pago 26
    condicion = m.CondicionCredito(
        cliente_id=cliente.id_cliente, moneda_id=moneda.id_moneda,
        tasa_compensatoria=D("24"), tipo_tasa_comp=TipoTasa.NOMINAL, plazo_tasa_comp_dias=360, capitaliz_comp_dias=30,
        tasa_moratoria=D("12"), tipo_tasa_mora=TipoTasa.NOMINAL, plazo_tasa_mora_dias=360, capitaliz_mora_dias=1,
        limite_credito=D("2000"), max_meses=12, dia_corte=20, dia_pago=26, vigente_desde=date(2026, 1, 1),
    )
    s.add(condicion)
    s.flush()

    def compra(modalidad, monto, cuotas=1):
        c = m.Compra(cliente_id=cliente.id_cliente, condicion_id=condicion.id_condicion,
                     fecha_hora_compra=datetime(2026, 10, 5, tzinfo=timezone.utc), modalidad=modalidad,
                     num_cuotas=cuotas, monto_total=monto, tep_aplicada=D("2"),
                     fecha_corte_asignada=date(2026, 10, 20), fecha_primer_pago=date(2026, 10, 26),
                     dias_gracia=21, capital_capitalizado=monto)
        s.add(c)
        s.flush()
        return c

    fin_de_mes = compra(ModalidadCompra.FIN_DE_MES, D("800.00"))
    en_cuotas = compra(ModalidadCompra.CUOTAS, D("200.00"), cuotas=2)
    cuotas = [
        m.Cuota(compra_id=en_cuotas.id_compra, numero_cuota=n, fecha_vencimiento=date(2026, 9 + n, 26),
                saldo_inicial=D("100"), interes=D("2"), amortizacion=D("100"), monto_cuota=D("102"), saldo_final=D("0"))
        for n in (1, 2)
    ]
    s.add_all(cuotas)
    s.flush()
    estado = m.EstadoCuenta(cliente_id=cliente.id_cliente, anio=2026, mes=10, fecha_corte=date(2026, 10, 20),
                            fecha_pago=date(2026, 10, 26), total_capital=D("900.00"), total_interes_comp=D("14.95"),
                            total_pagar=D("914.95"))
    s.add(estado)
    s.flush()
    s.add_all([
        m.EstadoCuentaDetalle(estado_cuenta_id=estado.id_estado_cuenta, compra_id=fin_de_mes.id_compra,
                              tipo_item=TipoItemEstadoCuenta.COMPRA, monto=D("800.00"), orden=1),
        m.EstadoCuentaDetalle(estado_cuenta_id=estado.id_estado_cuenta, compra_id=en_cuotas.id_compra,
                              cuota_id=cuotas[0].id_cuota, tipo_item=TipoItemEstadoCuenta.CUOTA, monto=D("102.00"), orden=2),
    ])
    s.commit()
    ids = dict(estado=estado.id_estado_cuenta, admin=admin.id_usuario, fin_de_mes=fin_de_mes.id_compra,
               en_cuotas=en_cuotas.id_compra, cuota1=cuotas[0].id_cuota, cuota2=cuotas[1].id_cuota)
    s.close()

    def sesion_prueba():
        sesion = Sesion()
        try:
            yield sesion
        finally:
            sesion.close()

    app.dependency_overrides[obtener_sesion] = sesion_prueba
    yield TestClient(app), Sesion, ids
    app.dependency_overrides.clear()


def pagar(cliente, ids, monto, fecha="2026-10-31"):
    return cliente.post(f"{URL}/{ids['estado']}", json={"usuario_id": ids["admin"], "monto_pagado": monto, "fecha_pago": fecha})


def test_exigible_con_cuatro_dias_de_mora(entorno):
    cliente, _, ids = entorno
    r = cliente.get(f"{URL}/{ids['estado']}/exigible", params={"fecha_pago": "2026-10-31"}).json()
    assert r["dias_mora"] == 4
    assert D(r["interes_mora"]) == D("1.22")
    assert D(r["total_exigible"]) == D("916.17")


def test_pago_exacto_aplica_mora_interes_y_capital(entorno):
    cliente, Sesion, ids = entorno
    r = pagar(cliente, ids, "916.17")
    assert r.status_code == 201
    j = r.json()
    assert (D(j["aplicado_mora"]), D(j["aplicado_interes_comp"]), D(j["aplicado_capital"])) == (D("1.22"), D("14.95"), D("900.00"))
    assert D(j["excedente_devuelto"]) == 0 and j["estado_cuenta"] == "PAGADO"

    s = Sesion()
    pago = s.get(m.Pago, j["id_pago"])
    assert pago.monto_pagado == D("916.17") and pago.monto_mora_aplicado == D("1.22")
    assert s.get(m.Compra, ids["fin_de_mes"]).estado == EstadoCompra.CANCELADA
    # la compra en cuotas sigue vigente: solo se pago la cuota facturada, no la futura
    assert s.get(m.Cuota, ids["cuota1"]).estado == EstadoCuota.PAGADA
    assert s.get(m.Cuota, ids["cuota2"]).estado == EstadoCuota.PENDIENTE
    assert s.get(m.Compra, ids["en_cuotas"]).estado == EstadoCompra.VIGENTE
    assert s.query(m.Bitacora).count() == 1
    s.close()


def test_pago_parcial_se_rechaza_y_no_registra_nada(entorno):
    cliente, Sesion, ids = entorno
    r = pagar(cliente, ids, "916.16")
    assert r.status_code == 400
    assert r.json()["detail"]["faltante"] == "0.01"
    s = Sesion()
    assert s.query(m.Pago).count() == 0 and s.get(m.EstadoCuenta, ids["estado"]).estado.value == "EMITIDO"
    s.close()


def test_excedente_se_devuelve_y_no_adelanta_cuotas(entorno):
    cliente, Sesion, ids = entorno
    j = pagar(cliente, ids, "1000.00").json()
    assert D(j["excedente_devuelto"]) == D("83.83") and D(j["monto_aplicado"]) == D("916.17")
    s = Sesion()
    assert s.get(m.Pago, j["id_pago"]).monto_pagado == D("916.17")
    assert s.get(m.Cuota, ids["cuota2"]).estado == EstadoCuota.PENDIENTE
    s.close()


def test_pago_puntual_no_tiene_mora(entorno):
    cliente, _, ids = entorno
    j = pagar(cliente, ids, "914.95", fecha="2026-10-26").json()
    assert j["dias_mora"] == 0 and D(j["aplicado_mora"]) == 0 and D(j["total_exigible"]) == D("914.95")


def test_no_se_paga_dos_veces_ni_estados_inexistentes(entorno):
    cliente, _, ids = entorno
    assert pagar(cliente, ids, "916.17").status_code == 201
    assert pagar(cliente, ids, "916.17").status_code == 409
    assert cliente.post(f"{URL}/9999", json={"usuario_id": ids["admin"], "monto_pagado": "10.00"}).status_code == 404
