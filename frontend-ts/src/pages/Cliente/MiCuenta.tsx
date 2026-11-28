import { useCallback, useState } from 'react'
import { useConsulta, useLista } from '../../api/consultas'
import { Shell } from '../../components/layout/Shell'
import { DetalleCompra } from '../../components/negocio/DetalleCompra'
import { TablaCronograma } from '../../components/negocio/TablaCronograma'
import { TarjetasEstadosCuenta } from '../../components/negocio/TarjetasEstadosCuenta'
import { Campo } from '../../components/ui/Campo'
import { Boton } from '../../components/ui/Boton'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import { Insignia } from '../../components/ui/Insignia'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Modal } from '../../components/ui/Modal'
import { Medidor } from '../../components/ui/Medidor'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { TarjetaKpi } from '../../components/ui/TarjetaKpi'
import type { Compra, EstadoCuenta } from '../../types/dominio'
import type { ResumenMiCuenta } from '../../types/resumen'
import { ESTADO_COMPRA, TIPO_TASA, nombreDelPlazo } from '../../utils/etiquetas'
import { formatearFecha, formatearMonto, formatearPorcentaje, formatearTasa, plural } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import pagina from '../../styles/pagina.module.css'
import styles from './MiCuenta.module.css'

export function MiCuenta() {
  const resumen = useConsulta<ResumenMiCuenta>('/mi-cuenta/resumen')
  const compras = useLista<Compra>('/mi-cuenta/compras')
  const estados = useLista<EstadoCuenta>('/mi-cuenta/estados-cuenta')
  const [compraId, setCompraId] = useState<number>()
  const [compraDetalle, setCompraDetalle] = useState<Compra>()
  const cerrarDetalle = useCallback(() => setCompraDetalle(undefined), [])

  if (!resumen.datos) return <Shell titulo="Mi cuenta"><EstadoConsulta {...resumen} /></Shell>

  const { tienda, posicion, condicion, credito_disponible } = resumen.datos
  const comprasConCuotas = (compras.datos ?? []).filter((compra) => compra.cronograma.length > 0)
  const compraEnCuotas = comprasConCuotas.find((c) => c.id_compra === compraId)
    ?? comprasConCuotas.find((c) => c.estado === 'VIGENTE')
    ?? comprasConCuotas[0]
  const { proximo_vencimiento: proximo, monto_proximo_pago: montoProximo } = posicion
  const dinero = (valor: string | number) => formatearMonto(valor, posicion.moneda)
  const saldo = Number(posicion.saldo_capital)
  const limite = Number(condicion?.limite_credito ?? 0)

  return (
    <Shell titulo="Mi cuenta" subtitulo={'El detalle de tu crédito en ' + tienda + '.'}>
      <section className={pagina.indicadores3} aria-label="Resumen de tu crédito">
        <TarjetaKpi
          destacada
          etiqueta={posicion.situacion === 'EN_MORA' ? 'Pago vencido' : 'Próximo pago'}
          valor={montoProximo ? dinero(montoProximo) : '—'}
          icono="calendario"
          detalle={proximo ? (posicion.situacion === 'EN_MORA' ? 'Venció el ' : 'Vence el ') + formatearFecha(proximo) : 'No tienes pagos pendientes'}
        />
        <TarjetaKpi etiqueta="Saldo pendiente" valor={dinero(saldo)} icono="billete" detalle="Capital que te falta pagar" />
        <TarjetaKpi
          etiqueta="Crédito disponible"
          valor={credito_disponible === null ? '—' : dinero(credito_disponible)}
          icono="bolsa"
          detalle={condicion ? 'de ' + dinero(limite) + ' de límite' : 'Sin condición vigente'}
        />
      </section>

      {condicion && (
        <Tarjeta>
          <TarjetaEncabezado titulo="Uso de tu línea de crédito" descripcion={'Usas ' + formatearPorcentaje(limite > 0 ? saldo / limite : 0) + ' de tu límite.'} />
          <Medidor etiqueta="Uso de tu línea de crédito" valor={saldo} maximo={limite} textoValor={dinero(saldo) + ' de ' + dinero(limite)} />
          <div className={styles.extremos}>
            <span>{dinero(saldo)} usados</span>
            {credito_disponible !== null && <span>{dinero(credito_disponible)} disponibles</span>}
          </div>
        </Tarjeta>
      )}

      <div className={pagina.mitades}>
        {proximo && montoProximo && (
          <Tarjeta>
            <TarjetaEncabezado titulo={posicion.situacion === 'EN_MORA' ? 'Tu pago pendiente' : 'Detalle de tu próximo pago'} />
            <ListaDatos>
              <FilaDato etiqueta="Pagar hasta el" valor={formatearFecha(proximo)} />
              <FilaDato etiqueta="Total a pagar" valor={dinero(montoProximo)} enfasis />
              {Number(posicion.mora_acumulada) > 0 && (
                <FilaDato etiqueta="Mora acumulada en tu cuenta" valor={dinero(posicion.mora_acumulada)} tono="peligro" />
              )}
            </ListaDatos>
          </Tarjeta>
        )}
        {condicion && (
          <Tarjeta>
            <TarjetaEncabezado titulo="Condiciones de tu crédito" descripcion="Lo que pactaste con la tienda." />
            <ListaDatos>
              <FilaDato etiqueta={'Tasa compensatoria (' + TIPO_TASA[condicion.tasa_compensatoria.tipo].toLowerCase() + ' ' + nombreDelPlazo(condicion.tasa_compensatoria.plazo_dias) + ')'}
                valor={formatearTasa(condicion.tasa_compensatoria.tasa_pct)} />
              <FilaDato etiqueta={'Tasa moratoria (' + TIPO_TASA[condicion.tasa_moratoria.tipo].toLowerCase() + ' ' + nombreDelPlazo(condicion.tasa_moratoria.plazo_dias) + ')'}
                valor={formatearTasa(condicion.tasa_moratoria.tasa_pct)} />
              <FilaDato etiqueta="Cierre de tus compras" valor={'Día ' + condicion.dia_corte + ' a las ' + condicion.hora_corte.slice(0, 5)} />
              <FilaDato etiqueta="Pagas hasta el" valor={'Día ' + condicion.dia_pago + ' de cada mes'} />
              <FilaDato etiqueta="Máximo de cuotas" valor={plural(condicion.max_meses, 'cuota', 'cuotas')} />
            </ListaDatos>
          </Tarjeta>
        )}
      </div>

      <EstadoConsulta {...compras} />
      {compraEnCuotas && (
        <Tarjeta relleno="ninguno">
          <TarjetaEncabezado
            conRelleno
            titulo="Cronograma de tu compra en cuotas"
            descripcion={compraEnCuotas.items.map((item) => item.nombre).join(', ') + ' · ' + formatearFecha(compraEnCuotas.fecha_hora_compra)
              + ' · ' + plural(compraEnCuotas.dias_gracia, 'día de gracia', 'días de gracia')}
            accion={comprasConCuotas.length > 1 && (
              <Campo etiqueta="Compra" ayuda="Elige la compra cuyo cronograma quieres consultar." htmlFor="mi-cronograma">
                <select id="mi-cronograma" className="campo-entrada" value={compraEnCuotas.id_compra ?? ''}
                  onChange={(evento) => setCompraId(Number(evento.target.value))}>
                  {comprasConCuotas.map((compra) => (
                    <option key={compra.id_compra} value={compra.id_compra ?? ''}>{formatearFecha(compra.fecha_hora_compra)} · n.° {compra.id_compra}</option>
                  ))}
                </select>
              </Campo>
            )}
          />
          <TablaCronograma cuotas={compraEnCuotas.cronograma} moneda={compraEnCuotas.moneda.codigo_iso} tcea={compraEnCuotas.tcea_pct} />
        </Tarjeta>
      )}

      {compras.datos && (
        <Tarjeta relleno="ninguno">
          <TarjetaEncabezado conRelleno titulo="Historial de compras" descripcion="De lo más reciente a lo más antiguo." />
          {compras.datos.length === 0 ? <p className={tabla.vacio}>Todavía no tienes compras a crédito.</p> : (
            <div className={tabla.envoltura}>
              <table className={tabla.tabla}>
                <thead>
                  <tr>
                    <th>Fecha</th><th>Productos</th><th>Forma de pago</th>
                    <th className={tabla.numerica}>Total</th><th>Estado</th>
                    <th><span className="solo-lectores">Detalle</span></th>
                  </tr>
                </thead>
                <tbody>
                  {compras.datos.map((compra) => (
                    <tr key={compra.id_compra}>
                      <td className={tabla.sinCorte}>{formatearFecha(compra.fecha_hora_compra)}</td>
                      <td className={tabla.celdaSecundaria}>{compra.items.map((detalle) => detalle.nombre).join(', ')}</td>
                      <td className={tabla.sinCorte}>{compra.modalidad === 'CUOTAS' ? plural(compra.num_cuotas, 'cuota', 'cuotas') : 'Fin de mes'}</td>
                      <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearMonto(compra.monto_total, compra.moneda.codigo_iso)}</td>
                      <td>{compra.estado && <Insignia texto={ESTADO_COMPRA[compra.estado].texto} tono={ESTADO_COMPRA[compra.estado].tono} />}</td>
                      <td><Boton variante="fantasma" tamano="pequeno" onClick={() => setCompraDetalle(compra)}>Ver detalle</Boton></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Tarjeta>
      )}

      {compraDetalle && (
        <Modal titulo="Detalle de compra" descripcion={compraDetalle.items.map((item) => item.nombre).join(', ')}
          onCerrar={cerrarDetalle} ancho={compraDetalle.cronograma.length ? 950 : 560}>
          <DetalleCompra compra={compraDetalle} />
        </Modal>
      )}

      <div className={pagina.tituloSeccion}>
        <h2>Mis estados de cuenta</h2>
        <p>Abre un estado para revisar sus compras, cuotas e intereses.</p>
      </div>
      <EstadoConsulta {...estados} />
      {estados.datos?.length === 0 && <Tarjeta><p className={tabla.vacio}>Todavía no se han emitido estados de cuenta.</p></Tarjeta>}
      {estados.datos && <TarjetasEstadosCuenta estados={estados.datos} ruta="/mi-cuenta/estados-cuenta" vistaCliente />}
    </Shell>
  )
}
