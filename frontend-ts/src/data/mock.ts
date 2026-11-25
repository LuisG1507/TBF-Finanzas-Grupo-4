/*
  Datos de muestra para las pantallas (todavía no conectadas al backend).

  Cuentan una sola historia coherente: la Bodega Don Rosendo al 15 de noviembre de 2026.
  Los totales del tablero se calculan a partir de estas listas, así que siempre cuadran entre sí.

  Las cifras con interés compensatorio salen del motor del backend (Backend-Grupo4):
  - La compra en cuotas de Juan es el caso validado de POST /api/v1/finanzas/frances:
    S/ 1,000 · TNA 24 % capitalizable cada 30 días · 3 cuotas · 11 días de gracia → cuota S/ 349.28.
  - Las compras a fin de mes usan S = C·(1 + TEP)^(días / días de la TEP).
  La mora, en cambio, es un valor de ejemplo: su fórmula todavía no está definida en el backend.
*/

import type { Cliente, Compra, Cuota, EstadoCuenta, Marca, Pago, Producto, Proveedor, Tienda, UnidadMedida } from '../types/dominio'
import type { CierreMensual, CobranzaSemanal, CuotaDelMes, PosicionCliente } from '../types/resumen'

/** El "hoy" de la demostración. */
export const HOY_DEMO = '2026-11-15'

export const TIENDA_DEMO = 'Bodega Don Rosendo'

/** El cliente con el que entra el perfil "Cliente" en la demostración. */
export const CLIENTE_DEMO_ID = 1

export const tiendasDemo: Tienda[] = [
  {
    id_tienda: 1,
    ruc: '10458963201',
    razon_social: 'Rosa Elvira Quispe Mamani',
    nombre_comercial: 'Bodega Don Rosendo',
    giro: 'Bodega',
    direccion: 'Jr. Los Sauces 452, San Juan de Lurigancho',
    telefono: '987 654 321',
    activo: true,
  },
  {
    id_tienda: 2,
    ruc: '20604187325',
    razon_social: 'Panificadora Aurora E.I.R.L.',
    nombre_comercial: 'Panadería Aurora',
    giro: 'Panadería',
    direccion: 'Av. Central 118, Comas',
    telefono: '956 112 233',
    email: 'contacto@panaderiaaurora.example',
    activo: true,
  },
  {
    id_tienda: 3,
    ruc: '20604518732',
    razon_social: 'Carnes y Embutidos El Buen Corte S.A.C.',
    nombre_comercial: 'Carnicería El Buen Corte',
    giro: 'Carnicería',
    direccion: 'Mercado Santa Rosa, puesto 14, Villa El Salvador',
    telefono: '933 410 275',
    activo: true,
  },
  {
    id_tienda: 4,
    ruc: '10407765123',
    razon_social: 'Julia Mercedes Chávez Rojas',
    nombre_comercial: 'Bazar Santa Julia',
    giro: 'Bazar',
    direccion: 'Av. Los Héroes 730, San Juan de Miraflores',
    telefono: '912 300 118',
    activo: true,
  },
  {
    id_tienda: 5,
    ruc: '10498712340',
    razon_social: 'Milagros Torres Cabrera',
    nombre_comercial: 'Peluquería Milagros',
    giro: 'Peluquería',
    telefono: '944 778 100',
    activo: false,
  },
]

export const proveedoresDemo: Proveedor[] = [
  { id_proveedor: 1, razon_social: 'Distribuidora San Fernando S.A.' },
  { id_proveedor: 2, razon_social: 'Mayorista Los Andes S.A.C.' },
]

export const marcasDemo: Marca[] = [
  { id_marca: 1, nombre: 'Gloria' },
  { id_marca: 2, nombre: 'Primor' },
  { id_marca: 3, nombre: 'Coldex' },
  { id_marca: 4, nombre: 'Oster' },
]

export const unidadesDemo: UnidadMedida[] = [
  { id_unidad: 1, codigo: 'UND', nombre: 'Unidad' },
  { id_unidad: 2, codigo: 'KG', nombre: 'Kilogramo' },
  { id_unidad: 3, codigo: 'LT', nombre: 'Litro' },
]

export const productosDemo: Producto[] = [
  {
    id_producto: 1,
    codigo: 'P-001',
    nombre: 'Leche evaporada Gloria 400 g',
    proveedor_id: 1,
    marca_id: 1,
    unidad_id: 1,
    precio_contado: '4.20',
    precio_lista: '4.60',
    permite_fin_de_mes: true,
    permite_cuotas: false,
    activo: true,
  },
  {
    id_producto: 2,
    codigo: 'P-002',
    nombre: 'Arroz extra a granel',
    proveedor_id: 2,
    unidad_id: 2,
    precio_contado: '3.80',
    precio_lista: '4.20',
    permite_fin_de_mes: true,
    permite_cuotas: false,
    activo: true,
  },
  {
    id_producto: 3,
    codigo: 'P-003',
    nombre: 'Aceite vegetal Primor 1 L',
    proveedor_id: 1,
    marca_id: 2,
    unidad_id: 1,
    precio_contado: '9.50',
    precio_lista: '10.40',
    permite_fin_de_mes: true,
    permite_cuotas: false,
    activo: true,
  },
  {
    id_producto: 4,
    codigo: 'P-004',
    nombre: 'Azúcar rubia a granel',
    proveedor_id: 2,
    unidad_id: 2,
    precio_contado: '3.60',
    precio_lista: '4.00',
    permite_fin_de_mes: true,
    permite_cuotas: false,
    activo: true,
  },
  {
    id_producto: 5,
    codigo: 'P-005',
    nombre: 'Refrigeradora Coldex 190 L',
    marca_id: 3,
    unidad_id: 1,
    precio_contado: '880.00',
    precio_lista: '1000.00',
    permite_fin_de_mes: false,
    permite_cuotas: true,
    activo: true,
  },
  {
    id_producto: 6,
    codigo: 'P-006',
    nombre: 'Licuadora Oster de 3 velocidades',
    marca_id: 4,
    unidad_id: 1,
    precio_contado: '189.00',
    precio_lista: '210.00',
    permite_fin_de_mes: true,
    permite_cuotas: true,
    activo: true,
  },
]

export const clientesDemo: Cliente[] = [
  {
    id_cliente: 1,
    tipo_documento: 'DNI',
    numero_documento: '45678912',
    nombres: 'Juan Carlos',
    apellidos: 'Ramírez Soto',
    telefono: '955 214 780',
    email: 'juan.ramirez@example.com',
    activo: true,
    condicion: {
      id_condicion: 1,
      cliente_id: 1,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '24.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '12.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '1500.00',
      max_meses: 6,
      dia_corte: 20,
      hora_corte: '00:00',
      dia_pago: 26,
    },
  },
  {
    id_cliente: 2,
    tipo_documento: 'DNI',
    numero_documento: '41235690',
    nombres: 'María Elena',
    apellidos: 'Torres Vidal',
    telefono: '998 765 432',
    activo: true,
    condicion: {
      id_condicion: 2,
      cliente_id: 2,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '26.0000000',
      tipo_tasa_comp: 'EFECTIVA',
      plazo_tasa_comp_dias: 360,
      tasa_moratoria: '12.0000000',
      tipo_tasa_mora: 'EFECTIVA',
      plazo_tasa_mora_dias: 360,
      limite_credito: '500.00',
      max_meses: 3,
      dia_corte: 15,
      hora_corte: '00:00',
      dia_pago: 22,
    },
  },
  {
    id_cliente: 3,
    tipo_documento: 'DNI',
    numero_documento: '70124583',
    nombres: 'Luis Alberto',
    apellidos: 'Huamán Ccori',
    telefono: '934 502 117',
    activo: true,
    condicion: {
      id_condicion: 3,
      cliente_id: 3,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '30.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '15.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '800.00',
      max_meses: 4,
      dia_corte: 28,
      hora_corte: '00:00',
      dia_pago: 5,
    },
  },
  {
    id_cliente: 4,
    tipo_documento: 'DNI',
    numero_documento: '09876541',
    nombres: 'Carmen Rosa',
    apellidos: 'Flores Díaz',
    telefono: '987 331 906',
    email: 'carmen.flores@example.com',
    activo: true,
    condicion: {
      id_condicion: 4,
      cliente_id: 4,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '2.0000000',
      tipo_tasa_comp: 'EFECTIVA',
      plazo_tasa_comp_dias: 30,
      tasa_moratoria: '1.0000000',
      tipo_tasa_mora: 'EFECTIVA',
      plazo_tasa_mora_dias: 30,
      limite_credito: '1200.00',
      max_meses: 6,
      dia_corte: 3,
      hora_corte: '00:00',
      dia_pago: 10,
    },
  },
  {
    id_cliente: 5,
    tipo_documento: 'DNI',
    numero_documento: '43120987',
    nombres: 'Pedro Pablo',
    apellidos: 'Mendoza Rojas',
    telefono: '921 664 038',
    activo: true,
    condicion: {
      id_condicion: 5,
      cliente_id: 5,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '24.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '12.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '600.00',
      max_meses: 3,
      dia_corte: 28,
      hora_corte: '00:00',
      dia_pago: 5,
    },
  },
  {
    id_cliente: 6,
    tipo_documento: 'DNI',
    numero_documento: '72561430',
    nombres: 'Ana Lucía',
    apellidos: 'Vargas Paredes',
    telefono: '945 870 223',
    activo: true,
    condicion: {
      id_condicion: 6,
      cliente_id: 6,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '24.0000000',
      tipo_tasa_comp: 'EFECTIVA',
      plazo_tasa_comp_dias: 360,
      tasa_moratoria: '10.0000000',
      tipo_tasa_mora: 'EFECTIVA',
      plazo_tasa_mora_dias: 360,
      limite_credito: '1000.00',
      max_meses: 6,
      dia_corte: 1,
      hora_corte: '00:00',
      dia_pago: 8,
    },
  },
  {
    id_cliente: 7,
    tipo_documento: 'DNI',
    numero_documento: '40718265',
    nombres: 'José Miguel',
    apellidos: 'Castillo León',
    telefono: '962 415 590',
    email: 'jose.castillo@example.com',
    activo: true,
    condicion: {
      id_condicion: 7,
      cliente_id: 7,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '22.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '11.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '2000.00',
      max_meses: 12,
      dia_corte: 5,
      hora_corte: '00:00',
      dia_pago: 12,
    },
  },
  {
    id_cliente: 8,
    tipo_documento: 'CE',
    numero_documento: '001245789',
    nombres: 'Teresa',
    apellidos: 'Gutiérrez Salas',
    telefono: '917 208 446',
    activo: true,
    condicion: {
      id_condicion: 8,
      cliente_id: 8,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '28.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '14.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '400.00',
      max_meses: 2,
      dia_corte: 28,
      hora_corte: '00:00',
      dia_pago: 5,
    },
  },
  {
    id_cliente: 9,
    tipo_documento: 'DNI',
    numero_documento: '46350127',
    nombres: 'Rosa Milagros',
    apellidos: 'Paredes Quinto',
    activo: false,
    condicion: {
      id_condicion: 9,
      cliente_id: 9,
      moneda_codigo: 'PEN',
      tasa_compensatoria: '24.0000000',
      tipo_tasa_comp: 'NOMINAL',
      plazo_tasa_comp_dias: 360,
      capitaliz_comp_dias: 30,
      tasa_moratoria: '12.0000000',
      tipo_tasa_mora: 'NOMINAL',
      plazo_tasa_mora_dias: 360,
      capitaliz_mora_dias: 30,
      limite_credito: '300.00',
      max_meses: 2,
      dia_corte: 20,
      hora_corte: '00:00',
      dia_pago: 26,
    },
  },
]

export const comprasDemo: Compra[] = [
  {
    // Caso validado contra el motor: C' = 1000 · 1.02^(11/30) = 1007.29 → cuota 349.28
    id_compra: 1,
    cliente_id: 1,
    fecha_hora_compra: '2026-09-15T18:30:00',
    modalidad: 'CUOTAS',
    num_cuotas: 3,
    monto_total: '1000.00',
    fecha_corte_asignada: '2026-09-20',
    fecha_primer_pago: '2026-10-26',
    dias_gracia: 11,
    capital_capitalizado: '1007.29',
    estado: 'VIGENTE',
    detalles: [{ id_detalle: 1, producto_id: 5, cantidad: '1.000', precio_unitario: '1000.00', subtotal: '1000.00' }],
  },
  {
    id_compra: 2,
    cliente_id: 2,
    fecha_hora_compra: '2026-11-03T09:12:00',
    modalidad: 'FIN_DE_MES',
    num_cuotas: 1,
    monto_total: '46.40',
    fecha_corte_asignada: '2026-11-15',
    fecha_primer_pago: '2026-11-22',
    dias_gracia: 0,
    capital_capitalizado: '46.40',
    estado: 'VIGENTE',
    detalles: [
      { id_detalle: 2, producto_id: 1, cantidad: '6.000', precio_unitario: '4.60', subtotal: '27.60' },
      { id_detalle: 3, producto_id: 2, cantidad: '2.000', precio_unitario: '4.20', subtotal: '8.40' },
      { id_detalle: 4, producto_id: 3, cantidad: '1.000', precio_unitario: '10.40', subtotal: '10.40' },
    ],
  },
  {
    id_compra: 3,
    cliente_id: 2,
    fecha_hora_compra: '2026-11-10T17:40:00',
    modalidad: 'FIN_DE_MES',
    num_cuotas: 1,
    monto_total: '40.00',
    fecha_corte_asignada: '2026-11-15',
    fecha_primer_pago: '2026-11-22',
    dias_gracia: 0,
    capital_capitalizado: '40.00',
    estado: 'VIGENTE',
    detalles: [{ id_detalle: 5, producto_id: 4, cantidad: '10.000', precio_unitario: '4.00', subtotal: '40.00' }],
  },
  {
    id_compra: 4,
    cliente_id: 1,
    fecha_hora_compra: '2026-07-08T11:05:00',
    modalidad: 'FIN_DE_MES',
    num_cuotas: 1,
    monto_total: '95.00',
    fecha_corte_asignada: '2026-07-20',
    fecha_primer_pago: '2026-07-26',
    dias_gracia: 0,
    capital_capitalizado: '95.00',
    estado: 'CANCELADA',
    detalles: [
      { id_detalle: 6, producto_id: 3, cantidad: '5.000', precio_unitario: '10.40', subtotal: '52.00' },
      { id_detalle: 7, producto_id: 1, cantidad: '5.000', precio_unitario: '4.60', subtotal: '23.00' },
      { id_detalle: 8, producto_id: 4, cantidad: '5.000', precio_unitario: '4.00', subtotal: '20.00' },
    ],
  },
]

/** Cronograma de la compra 1, tal como lo devuelve el motor (método francés, TEP 2 %). */
export const cuotasDemo: Cuota[] = [
  {
    id_cuota: 1,
    compra_id: 1,
    numero_cuota: 1,
    fecha_vencimiento: '2026-10-26',
    saldo_inicial: '1007.29',
    interes: '20.15',
    amortizacion: '329.13',
    monto_cuota: '349.28',
    saldo_final: '678.16',
    estado: 'PAGADA',
  },
  {
    id_cuota: 2,
    compra_id: 1,
    numero_cuota: 2,
    fecha_vencimiento: '2026-11-26',
    saldo_inicial: '678.16',
    interes: '13.56',
    amortizacion: '335.72',
    monto_cuota: '349.28',
    saldo_final: '342.44',
    estado: 'PENDIENTE',
  },
  {
    id_cuota: 3,
    compra_id: 1,
    numero_cuota: 3,
    fecha_vencimiento: '2026-12-26',
    saldo_inicial: '342.44',
    interes: '6.85',
    amortizacion: '342.44',
    monto_cuota: '349.29', // la última cuota absorbe el céntimo de redondeo
    saldo_final: '0.00',
    estado: 'PENDIENTE',
  },
]

export const estadosCuentaDemo: EstadoCuenta[] = [
  {
    // Fin de mes: 46.40 por 19 días + 40.00 por 12 días, a TEA 26 % → interés 0.57 + 0.31
    id_estado_cuenta: 1,
    cliente_id: 2,
    anio: 2026,
    mes: 11,
    fecha_corte: '2026-11-15',
    fecha_pago: '2026-11-22',
    total_capital: '86.40',
    total_interes_comp: '0.88',
    total_interes_mora: '0.00',
    total_pagar: '87.28',
    estado: 'EMITIDO',
    detalles: [
      { id_detalle_ec: 1, tipo_item: 'COMPRA', fecha_referencia: '2026-11-03', dias_transcurridos: 19, monto: '46.40', orden: 1 },
      { id_detalle_ec: 2, tipo_item: 'COMPRA', fecha_referencia: '2026-11-10', dias_transcurridos: 12, monto: '40.00', orden: 2 },
      { id_detalle_ec: 3, tipo_item: 'INT_COMPENSATORIO', tasa_aplicada: '26.0000000', monto: '0.88', orden: 3 },
    ],
  },
  {
    // Cuota 2 de 4 por el método francés (saldo 412.50, TEP 2.5 %) + 10 días de mora
    id_estado_cuenta: 2,
    cliente_id: 3,
    anio: 2026,
    mes: 11,
    fecha_corte: '2026-10-28',
    fecha_pago: '2026-11-05',
    total_capital: '134.12',
    total_interes_comp: '10.31',
    total_interes_mora: '1.85',
    total_pagar: '146.28',
    estado: 'VENCIDO',
    detalles: [
      { id_detalle_ec: 4, tipo_item: 'CUOTA', fecha_referencia: '2026-11-05', dias_transcurridos: 30, tasa_aplicada: '30.0000000', monto: '144.43', orden: 1 },
      { id_detalle_ec: 5, tipo_item: 'INT_MORATORIO', fecha_referencia: '2026-11-15', dias_transcurridos: 10, tasa_aplicada: '15.0000000', monto: '1.85', orden: 2 },
    ],
  },
  {
    id_estado_cuenta: 3,
    cliente_id: 5,
    anio: 2026,
    mes: 10,
    fecha_corte: '2026-09-28',
    fecha_pago: '2026-10-05',
    total_capital: '238.90',
    total_interes_comp: '3.65',
    total_interes_mora: '6.40',
    total_pagar: '248.95',
    estado: 'VENCIDO',
    detalles: [
      { id_detalle_ec: 6, tipo_item: 'COMPRA', fecha_referencia: '2026-09-12', dias_transcurridos: 23, monto: '238.90', orden: 1 },
      { id_detalle_ec: 7, tipo_item: 'INT_COMPENSATORIO', tasa_aplicada: '24.0000000', monto: '3.65', orden: 2 },
      { id_detalle_ec: 8, tipo_item: 'INT_MORATORIO', fecha_referencia: '2026-11-15', dias_transcurridos: 40, tasa_aplicada: '12.0000000', monto: '6.40', orden: 3 },
    ],
  },
  {
    id_estado_cuenta: 4,
    cliente_id: 8,
    anio: 2026,
    mes: 9,
    fecha_corte: '2026-08-28',
    fecha_pago: '2026-09-05',
    total_capital: '164.30',
    total_interes_comp: '2.67',
    total_interes_mora: '9.75',
    total_pagar: '176.72',
    estado: 'VENCIDO',
    detalles: [
      { id_detalle_ec: 9, tipo_item: 'COMPRA', fecha_referencia: '2026-08-14', dias_transcurridos: 21, monto: '164.30', orden: 1 },
      { id_detalle_ec: 10, tipo_item: 'INT_COMPENSATORIO', tasa_aplicada: '28.0000000', monto: '2.67', orden: 2 },
      { id_detalle_ec: 11, tipo_item: 'INT_MORATORIO', fecha_referencia: '2026-11-15', dias_transcurridos: 70, tasa_aplicada: '14.0000000', monto: '9.75', orden: 3 },
    ],
  },
]

export const pagosDemo: Pago[] = [
  {
    id_pago: 1,
    cliente_id: 4,
    fecha_hora_pago: '2026-11-10T10:20:00',
    monto_pagado: '251.30',
    monto_mora_aplicado: '0.00',
    monto_interes_comp_aplicado: '23.65',
    monto_capital_aplicado: '227.65',
    estado: 'REGISTRADO',
  },
]

/* ---------- Resumen para el tablero del negocio ---------- */

/** Cómo está la cuenta de cada cliente activo al día de hoy. Los cierres previos van de junio a octubre. */
export const posicionesDemo: PosicionCliente[] = [
  {
    cliente_id: 1,
    saldo_capital: '678.16',
    mora_acumulada: '0.00',
    dias_atraso: 0,
    situacion: 'AL_DIA',
    proximo_vencimiento: '2026-11-26',
    monto_proximo_pago: '349.28',
    saldos_cierre_previos: ['240.00', '180.50', '95.00', '1007.29', '678.16'],
  },
  {
    cliente_id: 2,
    saldo_capital: '86.40',
    mora_acumulada: '0.00',
    dias_atraso: 0,
    situacion: 'POR_VENCER',
    proximo_vencimiento: '2026-11-22',
    monto_proximo_pago: '87.28',
    saldos_cierre_previos: ['60.20', '74.80', '52.10', '91.30', '68.50'],
  },
  {
    cliente_id: 3,
    saldo_capital: '412.50',
    mora_acumulada: '1.85',
    dias_atraso: 10,
    situacion: 'EN_MORA',
    proximo_vencimiento: '2026-11-05',
    monto_proximo_pago: '146.28',
    saldos_cierre_previos: ['0.00', '150.00', '320.40', '543.34', '412.50'],
  },
  {
    cliente_id: 4,
    saldo_capital: '955.00',
    mora_acumulada: '0.00',
    dias_atraso: 0,
    situacion: 'AL_DIA',
    proximo_vencimiento: '2026-12-10',
    monto_proximo_pago: '251.30',
    saldos_cierre_previos: ['0.00', '0.00', '1180.00', '1190.60', '1182.65'],
  },
  {
    cliente_id: 5,
    saldo_capital: '238.90',
    mora_acumulada: '6.40',
    dias_atraso: 40,
    situacion: 'EN_MORA',
    proximo_vencimiento: '2026-10-05',
    monto_proximo_pago: '248.95',
    saldos_cierre_previos: ['85.00', '110.30', '96.40', '238.90', '238.90'],
  },
  {
    cliente_id: 6,
    saldo_capital: '0.00',
    mora_acumulada: '0.00',
    dias_atraso: 0,
    situacion: 'AL_DIA',
    saldos_cierre_previos: ['470.50', '378.90', '285.60', '190.50', '94.20'],
  },
  {
    cliente_id: 7,
    saldo_capital: '1420.75',
    mora_acumulada: '0.00',
    dias_atraso: 0,
    situacion: 'AL_DIA',
    proximo_vencimiento: '2026-12-12',
    monto_proximo_pago: '318.45',
    saldos_cierre_previos: ['980.00', '1250.40', '1105.30', '1890.00', '1712.60'],
  },
  {
    cliente_id: 8,
    saldo_capital: '164.30',
    mora_acumulada: '9.75',
    dias_atraso: 70,
    situacion: 'EN_MORA',
    proximo_vencimiento: '2026-09-05',
    monto_proximo_pago: '176.72',
    saldos_cierre_previos: ['120.00', '140.60', '164.30', '164.30', '164.30'],
  },
]

/** Lo que vence en noviembre de 2026, cliente por cliente. */
export const cuotasDelMesDemo: CuotaDelMes[] = [
  { cliente_id: 3, fecha_vencimiento: '2026-11-05', monto: '144.43', estado: 'VENCIDA' },
  { cliente_id: 6, fecha_vencimiento: '2026-11-08', monto: '96.10', estado: 'PAGADA' },
  { cliente_id: 4, fecha_vencimiento: '2026-11-10', monto: '251.30', estado: 'PAGADA' },
  { cliente_id: 7, fecha_vencimiento: '2026-11-12', monto: '318.45', estado: 'PAGADA' },
  { cliente_id: 2, fecha_vencimiento: '2026-11-22', monto: '87.28', estado: 'FACTURADA' },
  { cliente_id: 1, fecha_vencimiento: '2026-11-26', monto: '349.28', estado: 'PENDIENTE' },
]

/** Cobranza de las últimas ocho semanas (lunes a domingo). La última es la semana en curso. */
export const cobranzaSemanalDemo: CobranzaSemanal[] = [
  { desde: '2026-09-21', hasta: '2026-09-27', programado: '412.30', cobrado: '412.30' },
  { desde: '2026-09-28', hasta: '2026-10-04', programado: '268.90', cobrado: '268.90' },
  { desde: '2026-10-05', hasta: '2026-10-11', programado: '659.10', cobrado: '416.55' },
  { desde: '2026-10-12', hasta: '2026-10-18', programado: '318.45', cobrado: '318.45' },
  { desde: '2026-10-19', hasta: '2026-10-25', programado: '190.20', cobrado: '190.20' },
  { desde: '2026-10-26', hasta: '2026-11-01', programado: '469.28', cobrado: '469.28' },
  { desde: '2026-11-02', hasta: '2026-11-08', programado: '240.53', cobrado: '96.10' },
  { desde: '2026-11-09', hasta: '2026-11-15', programado: '569.75', cobrado: '569.75' },
]

/** Cierres de junio a octubre, para la tendencia de los indicadores. */
export const cierresMensualesDemo: CierreMensual[] = [
  { mes: '2026-06-01', cuotas_programadas: '612.40', mora_acumulada: '0.00', clientes_activos: 5 },
  { mes: '2026-07-01', cuotas_programadas: '745.10', mora_acumulada: '0.00', clientes_activos: 5 },
  { mes: '2026-08-01', cuotas_programadas: '980.60', mora_acumulada: '0.00', clientes_activos: 6 },
  { mes: '2026-09-01', cuotas_programadas: '1105.30', mora_acumulada: '2.35', clientes_activos: 7 },
  { mes: '2026-10-01', cuotas_programadas: '1378.92', mora_acumulada: '9.60', clientes_activos: 7 },
]

/* ---------- Ayudas de búsqueda ---------- */

export function nombreCompleto(cliente: Cliente): string {
  return `${cliente.nombres} ${cliente.apellidos}`
}

export function clientePorId(idCliente: number): Cliente | undefined {
  return clientesDemo.find((cliente) => cliente.id_cliente === idCliente)
}

export function posicionDe(idCliente: number): PosicionCliente | undefined {
  return posicionesDemo.find((posicion) => posicion.cliente_id === idCliente)
}

export function nombreProducto(idProducto: number): string {
  return productosDemo.find((producto) => producto.id_producto === idProducto)?.nombre ?? 'Producto'
}

export function nombreMarca(idMarca?: number): string | undefined {
  return marcasDemo.find((marca) => marca.id_marca === idMarca)?.nombre
}

export function codigoUnidad(idUnidad: number): string {
  return unidadesDemo.find((unidad) => unidad.id_unidad === idUnidad)?.codigo ?? ''
}
