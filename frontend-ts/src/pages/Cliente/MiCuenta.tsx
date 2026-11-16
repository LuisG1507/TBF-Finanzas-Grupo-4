import { Shell } from '../../components/layout/Shell'
import { Insignia } from '../../components/ui/Insignia'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Medidor } from '../../components/ui/Medidor'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { TarjetaKpi } from '../../components/ui/TarjetaKpi'
import { CLIENTE_DEMO_ID, TIENDA_DEMO, clientePorId, comprasDemo, cuotasDemo, nombreProducto, posicionDe } from '../../data/mock'
import { ESTADO_COMPRA, ESTADO_CUOTA, TIPO_TASA, nombreDelPlazo } from '../../utils/etiquetas'
import { formatearFecha, formatearPorcentaje, formatearSoles, formatearTasa, plural, sumarMontos } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import pagina from '../../styles/pagina.module.css'
import styles from './MiCuenta.module.css'

export function MiCuenta() {
  const cliente = clientePorId(CLIENTE_DEMO_ID)
  const posicion = posicionDe(CLIENTE_DEMO_ID)

  if (!cliente || !posicion) {
    return (
      <Shell titulo="Mi cuenta">
        <Tarjeta>
          <p className={tabla.vacio}>No encontramos tu cuenta. Consulta con tu tienda.</p>
        </Tarjeta>
      </Shell>
    )
  }

  const { condicion } = cliente
  const misCompras = comprasDemo
    .filter((compra) => compra.cliente_id === CLIENTE_DEMO_ID)
    .sort((a, b) => b.fecha_hora_compra.localeCompare(a.fecha_hora_compra))
  const compraEnCuotas = misCompras.find((compra) => compra.modalidad === 'CUOTAS' && compra.estado === 'VIGENTE')
  const cronograma = compraEnCuotas ? cuotasDemo.filter((cuota) => cuota.compra_id === compraEnCuotas.id_compra) : []
  const proximaCuota = cronograma.find((cuota) => cuota.estado !== 'PAGADA')

  const limite = Number(condicion.limite_credito)
  const saldo = Number(posicion.saldo_capital)
  const disponible = sumarMontos([limite, -saldo])

  return (
    <Shell titulo="Mi cuenta" subtitulo={`El detalle de tu crédito en ${TIENDA_DEMO}.`}>
      <section className={pagina.indicadores3} aria-label="Resumen de tu crédito">
        <TarjetaKpi
          destacada
          etiqueta="Próximo pago"
          valor={proximaCuota ? formatearSoles(proximaCuota.monto_cuota) : formatearSoles(0)}
          icono="calendario"
          variacion={
            proximaCuota ? { texto: `Cuota ${proximaCuota.numero_cuota} de ${cronograma.length}`, tono: 'neutro' } : undefined
          }
          detalle={proximaCuota ? `Vence el ${formatearFecha(proximaCuota.fecha_vencimiento)}` : 'No tienes pagos pendientes'}
        />
        <TarjetaKpi etiqueta="Saldo pendiente" valor={formatearSoles(saldo)} icono="billete" detalle="Capital que te falta pagar" />
        <TarjetaKpi
          etiqueta="Crédito disponible"
          valor={formatearSoles(disponible)}
          icono="bolsa"
          detalle={`de ${formatearSoles(limite)} de límite`}
        />
      </section>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Uso de tu línea de crédito"
          descripcion={`Usas ${formatearPorcentaje(limite > 0 ? saldo / limite : 0)} de tu límite.`}
        />
        <Medidor
          etiqueta="Uso de tu línea de crédito"
          valor={saldo}
          maximo={limite}
          textoValor={`${formatearSoles(saldo)} de ${formatearSoles(limite)}`}
        />
        <div className={styles.extremos}>
          <span>{formatearSoles(saldo)} usados</span>
          <span>{formatearSoles(disponible)} disponibles</span>
        </div>
      </Tarjeta>

      <div className={pagina.mitades}>
        {proximaCuota && (
          <Tarjeta>
            <TarjetaEncabezado
              titulo="Detalle de tu próximo pago"
              descripcion={`Es el monto exacto que debes pagar el ${formatearFecha(proximaCuota.fecha_vencimiento)}.`}
            />
            <ListaDatos>
              <FilaDato etiqueta="Amortización de capital" valor={formatearSoles(proximaCuota.amortizacion)} />
              <FilaDato etiqueta="Interés compensatorio" valor={formatearSoles(proximaCuota.interes)} />
              {Number(posicion.mora_acumulada) > 0 && (
                <FilaDato etiqueta="Interés moratorio" valor={formatearSoles(posicion.mora_acumulada)} tono="peligro" />
              )}
              <FilaDato etiqueta="Total a pagar" valor={formatearSoles(proximaCuota.monto_cuota)} enfasis separada />
            </ListaDatos>
          </Tarjeta>
        )}

        <Tarjeta>
          <TarjetaEncabezado titulo="Condiciones de tu crédito" descripcion="Lo que pactaste con la tienda." />
          <ListaDatos>
            <FilaDato
              etiqueta={`Tasa compensatoria (${TIPO_TASA[condicion.tipo_tasa_comp].toLowerCase()} ${nombreDelPlazo(condicion.plazo_tasa_comp_dias)})`}
              valor={formatearTasa(condicion.tasa_compensatoria)}
            />
            <FilaDato
              etiqueta={`Tasa moratoria (${TIPO_TASA[condicion.tipo_tasa_mora].toLowerCase()} ${nombreDelPlazo(condicion.plazo_tasa_mora_dias)})`}
              valor={formatearTasa(condicion.tasa_moratoria)}
            />
            <FilaDato etiqueta="Día de corte" valor={`Día ${condicion.dia_corte} de cada mes`} />
            <FilaDato etiqueta="Día de pago" valor={`Día ${condicion.dia_pago} de cada mes`} />
            <FilaDato etiqueta="Máximo de cuotas" valor={plural(condicion.max_meses, 'cuota', 'cuotas')} />
          </ListaDatos>
        </Tarjeta>
      </div>

      {compraEnCuotas && (
        <Tarjeta relleno="ninguno">
          <TarjetaEncabezado
            conRelleno
            titulo="Cronograma de tu compra en cuotas"
            descripcion={`${compraEnCuotas.detalles.map((detalle) => nombreProducto(detalle.producto_id)).join(', ')} · ${formatearSoles(compraEnCuotas.monto_total)} el ${formatearFecha(compraEnCuotas.fecha_hora_compra)}. Con ${plural(compraEnCuotas.dias_gracia, 'día', 'días')} de gracia, el capital quedó en ${formatearSoles(compraEnCuotas.capital_capitalizado)}.`}
          />
          <div className={tabla.envoltura}>
            <table className={[tabla.tabla, tabla.amplia].join(' ')}>
              <colgroup>
                <col style={{ width: '7%' }} />
                <col style={{ width: '15%' }} />
                <col style={{ width: '15%' }} />
                <col style={{ width: '11%' }} />
                <col style={{ width: '14%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '14%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>N.°</th>
                  <th>Vencimiento</th>
                  <th className={tabla.numerica}>Saldo inicial</th>
                  <th className={tabla.numerica}>Interés</th>
                  <th className={tabla.numerica}>Amortización</th>
                  <th className={tabla.numerica}>Cuota</th>
                  <th className={tabla.numerica}>Saldo final</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {cronograma.map((cuota) => (
                  <tr key={cuota.id_cuota}>
                    <td>{cuota.numero_cuota}</td>
                    <td className={tabla.sinCorte}>{formatearFecha(cuota.fecha_vencimiento)}</td>
                    <td className={tabla.numerica}>{formatearSoles(cuota.saldo_inicial)}</td>
                    <td className={tabla.numerica}>{formatearSoles(cuota.interes)}</td>
                    <td className={tabla.numerica}>{formatearSoles(cuota.amortizacion)}</td>
                    <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(cuota.monto_cuota)}</td>
                    <td className={tabla.numerica}>{formatearSoles(cuota.saldo_final)}</td>
                    <td>
                      <Insignia texto={ESTADO_CUOTA[cuota.estado].texto} tono={ESTADO_CUOTA[cuota.estado].tono} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Tarjeta>
      )}

      <Tarjeta relleno="ninguno">
        <TarjetaEncabezado conRelleno titulo="Historial de compras" descripcion="Todo lo que llevaste a crédito, de lo más reciente a lo más antiguo." />
        <div className={tabla.envoltura}>
          <table className={tabla.tabla}>
            <colgroup>
              <col style={{ width: '17%' }} />
              <col style={{ width: '37%' }} />
              <col style={{ width: '16%' }} />
              <col style={{ width: '15%' }} />
              <col style={{ width: '15%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Productos</th>
                <th>Forma de pago</th>
                <th className={tabla.numerica}>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {misCompras.map((compra) => (
                <tr key={compra.id_compra}>
                  <td className={tabla.sinCorte}>{formatearFecha(compra.fecha_hora_compra)}</td>
                  <td className={tabla.celdaSecundaria}>{compra.detalles.map((detalle) => nombreProducto(detalle.producto_id)).join(', ')}</td>
                  <td className={tabla.sinCorte}>
                    {compra.modalidad === 'CUOTAS' ? plural(compra.num_cuotas, 'cuota', 'cuotas') : 'Fin de mes'}
                  </td>
                  <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(compra.monto_total)}</td>
                  <td>
                    <Insignia texto={ESTADO_COMPRA[compra.estado].texto} tono={ESTADO_COMPRA[compra.estado].tono} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Tarjeta>
    </Shell>
  )
}
