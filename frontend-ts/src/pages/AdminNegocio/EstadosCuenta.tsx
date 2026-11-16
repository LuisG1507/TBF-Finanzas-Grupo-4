import { useState } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Avatar } from '../../components/ui/Avatar'
import { Icono } from '../../components/ui/Icono'
import { Insignia } from '../../components/ui/Insignia'
import { Segmentado, type OpcionSegmentado } from '../../components/ui/Segmentado'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { clientePorId, estadosCuentaDemo, nombreCompleto } from '../../data/mock'
import type { EstadoCuentaEstado } from '../../types/dominio'
import { ESTADO_CUENTA, TIPO_ITEM } from '../../utils/etiquetas'
import { formatearFecha, formatearSoles, formatearTasa, nombreDelMes } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import styles from './EstadosCuenta.module.css'

type Filtro = 'TODOS' | EstadoCuentaEstado

const FILTROS: OpcionSegmentado<Filtro>[] = [
  { valor: 'TODOS', etiqueta: 'Todos' },
  { valor: 'EMITIDO', etiqueta: 'Emitidos' },
  { valor: 'VENCIDO', etiqueta: 'Vencidos' },
  { valor: 'PAGADO', etiqueta: 'Pagados' },
]

const SIN_RESULTADOS: Record<Filtro, string> = {
  TODOS: 'Todavía no se ha emitido ningún estado de cuenta.',
  EMITIDO: 'No hay estados de cuenta emitidos pendientes de pago.',
  VENCIDO: 'No hay estados de cuenta vencidos.',
  PAGADO: 'No hay estados de cuenta pagados.',
}

/** "Noviembre de 2026" */
function periodo(anio: number, mes: number): string {
  const nombre = nombreDelMes(`${anio}-${String(mes).padStart(2, '0')}-01`)
  return `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} de ${anio}`
}

export function EstadosCuenta() {
  const [filtro, setFiltro] = useState<Filtro>('TODOS')
  const [expandidoId, setExpandidoId] = useState<number | null>(estadosCuentaDemo[0]?.id_estado_cuenta ?? null)

  const visibles = estadosCuentaDemo.filter((estadoCuenta) => filtro === 'TODOS' || estadoCuenta.estado === filtro)

  return (
    <Shell
      titulo="Estados de cuenta"
      subtitulo="El listado que se genera en cada fecha de corte, con la mora identificada aparte."
      acciones={<Segmentado etiquetaGrupo="Filtrar por estado" opciones={FILTROS} valor={filtro} onCambiar={setFiltro} />}
    >
      {visibles.length === 0 && (
        <Tarjeta>
          <p className={tabla.vacio}>{SIN_RESULTADOS[filtro]}</p>
        </Tarjeta>
      )}

      {visibles.map((estadoCuenta) => {
        const cliente = clientePorId(estadoCuenta.cliente_id)
        const nombre = cliente ? nombreCompleto(cliente) : 'Cliente'
        const expandido = expandidoId === estadoCuenta.id_estado_cuenta
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
                  <span className={styles.totalValor}>{formatearSoles(estadoCuenta.total_pagar)}</span>
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
                    <dd>{formatearSoles(estadoCuenta.total_capital)}</dd>
                  </div>
                  <div>
                    <dt>Interés compensatorio</dt>
                    <dd>{formatearSoles(estadoCuenta.total_interes_comp)}</dd>
                  </div>
                  <div className={tieneMora ? styles.conMora : undefined}>
                    <dt>Interés moratorio</dt>
                    <dd>{formatearSoles(estadoCuenta.total_interes_mora)}</dd>
                  </div>
                </dl>
                <div className={tabla.envoltura}>
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
                      {estadoCuenta.detalles
                        .slice()
                        .sort((a, b) => a.orden - b.orden)
                        .map((detalle) => (
                          <tr key={detalle.id_detalle_ec}>
                            <td>{detalle.orden}</td>
                            <td>
                              <Insignia
                                texto={TIPO_ITEM[detalle.tipo_item]}
                                tono={detalle.tipo_item === 'INT_MORATORIO' ? 'peligro' : 'neutro'}
                              />
                            </td>
                            <td className={tabla.sinCorte}>{detalle.fecha_referencia ? formatearFecha(detalle.fecha_referencia) : '—'}</td>
                            <td className={tabla.numerica}>{detalle.dias_transcurridos ?? '—'}</td>
                            <td className={tabla.numerica}>{detalle.tasa_aplicada ? formatearTasa(detalle.tasa_aplicada) : '—'}</td>
                            <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(detalle.monto)}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Tarjeta>
        )
      })}
    </Shell>
  )
}
