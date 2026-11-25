import { useState } from 'react'
import { useConsulta } from '../../api/consultas'
import type { EstadoCuenta, EstadoCuentaCompleto } from '../../types/dominio'
import { ESTADO_CUENTA } from '../../utils/etiquetas'
import { formatearFecha, formatearMonto, formatearTasa, nombreDelMes } from '../../utils/formato'
import { Avatar } from '../ui/Avatar'
import { EstadoConsulta } from '../ui/EstadoConsulta'
import { Icono } from '../ui/Icono'
import { Insignia } from '../ui/Insignia'
import { Tarjeta } from '../ui/Tarjeta'
import tabla from '../ui/Tabla.module.css'
import styles from '../../pages/AdminNegocio/EstadosCuenta.module.css'

function periodo(anio: number, mes: number): string {
  const nombre = nombreDelMes(`${anio}-${String(mes).padStart(2, '0')}-01`)
  return `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} de ${anio}`
}

export function TarjetasEstadosCuenta({ estados, ruta }: { estados: EstadoCuenta[]; ruta: string }) {
  const [expandidoId, setExpandidoId] = useState<number | null>()
  const seleccion = expandidoId === undefined ? estados[0]?.id_estado_cuenta : expandidoId
  const detalle = useConsulta<EstadoCuentaCompleto>(estados.some((e) => e.id_estado_cuenta === seleccion) ? ruta + '/' + seleccion : null)
  return (
    <>
      {estados.map((estadoCuenta) => {
        const nombre = estadoCuenta.cliente_nombre
        const moneda = estadoCuenta.moneda?.codigo_iso
        const expandido = seleccion === estadoCuenta.id_estado_cuenta
        const idDetalle = `estado-cuenta-${estadoCuenta.id_estado_cuenta}`
        const tieneMora = Number(estadoCuenta.total_interes_mora) > 0
        const presentacion = ESTADO_CUENTA[estadoCuenta.estado]

        return (
          <Tarjeta key={estadoCuenta.id_estado_cuenta} relleno="ninguno">
            <button
              type="button"
              className={styles.cabecera}
              aria-expanded={expandido}
              aria-controls={idDetalle}
              onClick={() => setExpandidoId(expandido ? null : estadoCuenta.id_estado_cuenta)}
            >
              <span className={styles.quien}>
                <Avatar nombre={nombre} />
                <span className={styles.quienTexto}>
                  <span className={styles.nombre}>{nombre}</span>
                  <span className={styles.fechas}>
                    {periodo(estadoCuenta.anio, estadoCuenta.mes)} · corte {formatearFecha(estadoCuenta.fecha_corte)} · pago{' '}
                    {formatearFecha(estadoCuenta.fecha_pago)}
                  </span>
                </span>
              </span>
              <span className={styles.resumen}>
                <span className={styles.total}>
                  <span className={styles.totalEtiqueta}>Total a pagar</span>
                  <span className={styles.totalValor}>{formatearMonto(estadoCuenta.total_pagar, moneda)}</span>
                </span>
                <Insignia texto={presentacion.texto} tono={presentacion.tono} />
                <Icono nombre="chevronAbajo" tamano={18} className={[styles.flecha, expandido && styles.flechaArriba].filter(Boolean).join(' ')} />
              </span>
            </button>

            {expandido && (
              <div id={idDetalle} className={styles.detalle}>
                <dl className={styles.totales}>
                  <div>
                    <dt>Capital</dt>
                    <dd>{formatearMonto(estadoCuenta.total_capital, moneda)}</dd>
                  </div>
                  <div>
                    <dt>Interés compensatorio</dt>
                    <dd>{formatearMonto(estadoCuenta.total_interes_comp, moneda)}</dd>
                  </div>
                  <div className={tieneMora ? styles.conMora : undefined}>
                    <dt>Interés moratorio</dt>
                    <dd>{formatearMonto(estadoCuenta.total_interes_mora, moneda)}</dd>
                  </div>
                </dl>
                <EstadoConsulta {...detalle} />
                {detalle.datos && <div className={tabla.envoltura}>
                  <table className={tabla.tabla}>
                    <colgroup>
                      <col style={{ width: '9%' }} />
                      <col style={{ width: '27%' }} />
                      <col style={{ width: '17%' }} />
                      <col style={{ width: '11%' }} />
                      <col style={{ width: '18%' }} />
                      <col style={{ width: '18%' }} />
                    </colgroup>
                    <thead>
                      <tr>
                        <th>N.°</th>
                        <th>Concepto</th>
                        <th>Fecha</th>
                        <th className={tabla.numerica}>Días</th>
                        <th className={tabla.numerica}>Tasa aplicada</th>
                        <th className={tabla.numerica}>Monto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detalle.datos.detalles
                        .slice()
                        .sort((a, b) => a.orden - b.orden)
                        .map((detalle) => (
                          <tr key={detalle.id_detalle_ec}>
                            <td>{detalle.orden}</td>
                            <td>
                              <Insignia
                                texto={detalle.concepto}
                                tono={detalle.tipo_item === 'INT_MORATORIO' ? 'peligro' : 'neutro'}
                              />
                            </td>
                            <td className={tabla.sinCorte}>{detalle.fecha_referencia ? formatearFecha(detalle.fecha_referencia) : '—'}</td>
                            <td className={tabla.numerica}>{detalle.dias_transcurridos ?? '—'}</td>
                            <td className={tabla.numerica}>{detalle.tasa_aplicada ? formatearTasa(detalle.tasa_aplicada) : '—'}</td>
                            <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearMonto(detalle.monto, moneda)}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>}
              </div>
            )}
          </Tarjeta>
        )
      })}
    </>
  )
}
