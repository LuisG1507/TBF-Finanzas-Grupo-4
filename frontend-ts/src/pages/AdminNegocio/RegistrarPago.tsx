import { useState } from 'react'
import { ErrorApi } from '../../api/cliente'
import { useAccion, useConsulta, useLista } from '../../api/consultas'
import { registrarPago, rutaExigible, type RespuestaExigible, type RespuestaPago } from '../../api/pagos'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import { Shell } from '../../components/layout/Shell'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import type { Cliente, EstadoCuenta } from '../../types/dominio'
import { nombreCompleto } from '../../utils/texto'
import { ESTADO_CUENTA } from '../../utils/etiquetas'
import { formatearFecha, formatearMonto, hoyLima, sumarMontos } from '../../utils/formato'
import pagina from '../../styles/pagina.module.css'
import styles from './RegistrarPago.module.css'

const SUBTITULO = 'Cobra el estado de cuenta de un cliente: Bizon calcula la mora del día y te dice cuánto vuelto dar.'

/** Orden en que se aplica un pago: mora, interés compensatorio y capital. */
const PRELACION = ['Interés moratorio', 'Interés compensatorio', 'Capital']

export function RegistrarPago() {
  const cargaClientes = useLista<Cliente>('/clientes?activo=true')
  const cargaEstados = useLista<EstadoCuenta>('/estados-cuenta')
  const clientesActivos = cargaClientes.datos ?? []
  const pendientes = (cargaEstados.datos ?? []).filter((estado) => estado.estado !== 'PAGADO')
    .sort((a, b) => a.fecha_pago.localeCompare(b.fecha_pago) || a.id_estado_cuenta - b.id_estado_cuenta)
  const [clienteId, setClienteId] = useState<number>()
  const [estadoId, setEstadoId] = useState<number>()
  const [monto, setMonto] = useState('')
  const [fechaPago, setFechaPago] = useState(hoyLima)
  const [pagado, setPagado] = useState<{ estado: EstadoCuenta; resultado: RespuestaPago } | null>(null)
  const accion = useAccion()

  const cliente = clientesActivos.find((c) => c.id_cliente === clienteId)
    ?? clientesActivos.find((c) => c.id_cliente === pendientes[0]?.cliente_id)
    ?? clientesActivos[0]
  const delCliente = pendientes.filter((e) => e.cliente_id === cliente?.id_cliente)
  const estadoCuenta = pagado?.estado ?? delCliente.find((e) => e.id_estado_cuenta === estadoId) ?? delCliente[0]
  const resultado = pagado?.resultado
  const pagoAceptado = Boolean(resultado)
  const consulta = useConsulta<RespuestaExigible>(
    !pagoAceptado && estadoCuenta && fechaPago ? rutaExigible(estadoCuenta.id_estado_cuenta, fechaPago) : null,
  )
  const exigible = resultado ?? consulta.datos
  const moneda = estadoCuenta?.moneda?.codigo_iso
  const dinero = (valor: string | number) => formatearMonto(valor, moneda)
  const interesMora = exigible?.interes_mora ?? '0'
  const totalAPagar = exigible?.total_exigible
  const tieneMora = Number(interesMora) > 0
  // Diferencia entre lo recibido y el total, en céntimos: negativa si falta, positiva si hay vuelto.
  const diferencia = !pagoAceptado && monto !== '' && totalAPagar ? sumarMontos([monto, -Number(totalAPagar)]) : null

  function reiniciar() {
    setMonto('')
    setPagado(null)
    accion.limpiarError()
  }

  function alRegistrar() {
    if (!estadoCuenta || !consulta.datos || !fechaPago) return
    void accion.ejecutar(async () => {
      try {
        const respuesta = await registrarPago(estadoCuenta.id_estado_cuenta, fechaPago, monto)
        setPagado({ estado: estadoCuenta, resultado: respuesta })
        cargaEstados.recargar()
      } catch (error) {
        if (error instanceof ErrorApi && error.detalle && typeof error.detalle === 'object' && 'faltante' in error.detalle) {
          throw new Error(error.message + '. Faltan ' + dinero(String(error.detalle.faltante)) + '.')
        }
        throw error
      }
    })
  }

  if (!cliente || (!cargaEstados.datos && !pagado)) {
    return (
      <Shell titulo="Registrar pago" subtitulo={SUBTITULO}>
        <EstadoConsulta {...cargaClientes} />
        <EstadoConsulta {...cargaEstados} />
        {cargaClientes.datos?.length === 0 && <Aviso tono="info">Todavía no hay clientes activos.</Aviso>}
      </Shell>
    )
  }

  return (
    <Shell titulo="Registrar pago" subtitulo={SUBTITULO}>
      <div className={pagina.dosColumnas}>
        <Tarjeta>
          <TarjetaEncabezado titulo="Pago del cliente" />
          <Campo etiqueta="Cliente" ayuda="Se muestra su estado de cuenta pendiente más antiguo." htmlFor="cliente_pago">
            <select
              id="cliente_pago"
              className="campo-entrada"
              value={cliente.id_cliente}
              disabled={accion.ocupado}
              onChange={(evento) => {
                setClienteId(Number(evento.target.value))
                setEstadoId(undefined)
                reiniciar()
              }}
            >
              {clientesActivos.map((opcion) => (
                <option key={opcion.id_cliente} value={opcion.id_cliente}>
                  {nombreCompleto(opcion)}
                </option>
              ))}
            </select>
          </Campo>

          {!pagoAceptado && delCliente.length > 1 && (
            <Campo etiqueta="Estado de cuenta a pagar" htmlFor="estado-pago">
              <select id="estado-pago" className="campo-entrada" value={estadoCuenta?.id_estado_cuenta ?? ''}
                disabled={accion.ocupado}
                onChange={(evento) => { setEstadoId(Number(evento.target.value)); reiniciar() }}>
                {delCliente.map((estado) => <option key={estado.id_estado_cuenta} value={estado.id_estado_cuenta}>
                  {formatearFecha(estado.fecha_pago)} · {formatearMonto(estado.total_pagar, estado.moneda?.codigo_iso)}
                </option>)}
              </select>
            </Campo>
          )}
          {!estadoCuenta ? (
            <div className={styles.bloque}>
              <Aviso tono="info" titulo={`${nombreCompleto(cliente)} no tiene nada por pagar`}>
                Los cobros aparecen aquí cuando se emite su estado de cuenta, en el cierre de mes siguiente a una compra. Un cliente recién
                registrado todavía no tiene compras.
              </Aviso>
            </div>
          ) : (
            <>
              <div className={styles.bloque}>
                <Campo
                  etiqueta="Fecha en que paga"
                  ayuda="Si paga después de la fecha pactada, el total suma la mora de esos días."
                  obligatorio
                  htmlFor="fecha_pago"
                >
                  <input
                    id="fecha_pago"
                    type="date"
                    className="campo-entrada"
                    value={fechaPago}
                    disabled={pagoAceptado || accion.ocupado}
                    onChange={(evento) => {
                      setFechaPago(evento.target.value)
                      accion.limpiarError()
                    }}
                  />
                </Campo>
              </div>

              <div className={styles.estadoCuenta}>
                <div className={styles.estadoCuentaCabecera}>
                  <p className={styles.estadoCuentaTitulo}>Estado de cuenta</p>
                  {pagoAceptado ? (
                    <Insignia texto={ESTADO_CUENTA.PAGADO.texto} tono={ESTADO_CUENTA.PAGADO.tono} />
                  ) : (
                    <Insignia texto={ESTADO_CUENTA[estadoCuenta.estado].texto} tono={ESTADO_CUENTA[estadoCuenta.estado].tono} />
                  )}
                </div>
                <ListaDatos>
                  <FilaDato etiqueta="Compras hasta el" valor={formatearFecha(estadoCuenta.fecha_corte)} />
                  <FilaDato etiqueta="Debía pagar hasta el" valor={formatearFecha(estadoCuenta.fecha_pago)} />
                  <FilaDato
                    etiqueta="Días de mora"
                    valor={exigible ? String(exigible.dias_mora) : '—'}
                    tono={tieneMora ? 'peligro' : undefined}
                  />
                  <FilaDato etiqueta="Capital" valor={dinero(estadoCuenta.total_capital)} separada />
                  <FilaDato etiqueta="Interés compensatorio" valor={dinero(estadoCuenta.total_interes_comp)} />
                  {exigible && Number(exigible.interes_comp_atraso) > 0 && (
                    <FilaDato etiqueta="Compensatorio por atraso" valor={dinero(exigible.interes_comp_atraso)} />
                  )}
                  <FilaDato etiqueta="Interés moratorio" valor={dinero(interesMora)} tono={tieneMora ? 'peligro' : undefined} />
                  <FilaDato etiqueta="Total a pagar" valor={totalAPagar ? dinero(totalAPagar) : '—'} enfasis separada />
                </ListaDatos>
              </div>

              <div className={styles.bloque}>
                <Campo
                  etiqueta={moneda === 'USD' ? 'Monto recibido (US$)' : 'Monto recibido (S/)'}
                  ayuda="Lo que te entrega el cliente. Debe cubrir el total a pagar."
                  obligatorio
                  htmlFor="monto"
                >
                  <input
                    id="monto"
                    type="number"
                    step="0.01"
                    min="0"
                    inputMode="decimal"
                    className="campo-entrada"
                    placeholder={totalAPagar}
                    value={monto}
                    disabled={pagoAceptado || accion.ocupado}
                    onChange={(evento) => {
                      setMonto(evento.target.value)
                      accion.limpiarError()
                    }}
                  />
                </Campo>
                {!pagoAceptado && totalAPagar && (
                  <div className={styles.ayudaMonto}>
                    <Boton variante="suave" tamano="pequeno" disabled={accion.ocupado}
                      onClick={() => { setMonto(totalAPagar); accion.limpiarError() }}>
                      Recibir el total exacto
                    </Boton>
                    {diferencia !== null && (
                      <p role="status" className={[styles.diferencia,
                        diferencia < 0 ? styles.diferenciaFalta : diferencia > 0 ? styles.diferenciaVuelto : ''].join(' ')}>
                        {diferencia < 0 ? 'Faltan ' + dinero(-diferencia) + ' para cubrir el total.'
                          : diferencia > 0 ? 'Vuelto para el cliente: ' + dinero(diferencia)
                            : 'Monto exacto, sin vuelto.'}
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className={[styles.bloque, pagina.pila].join(' ')}>
                <EstadoConsulta {...consulta} />
                <EstadoConsulta error={accion.error} />
                {resultado && (
                  <Aviso tono="exito" titulo="Pago registrado. Así se aplicó:">
                    <ol className={styles.aplicacion}>
                      <li>Interés moratorio: {dinero(resultado.aplicado_mora)}</li>
                      <li>Interés compensatorio: {dinero(resultado.aplicado_interes_comp)}</li>
                      <li>Capital: {dinero(resultado.aplicado_capital)}</li>
                    </ol>
                    {Number(resultado.excedente_devuelto) > 0 && (
                      <p>Devuelve al cliente {dinero(resultado.excedente_devuelto)} de excedente.</p>
                    )}
                  </Aviso>
                )}

                {pagoAceptado ? (
                  <Boton anchoCompleto onClick={reiniciar}>
                    Registrar otro pago
                  </Boton>
                ) : (
                  <Boton anchoCompleto onClick={alRegistrar} disabled={monto === '' || Number(monto) <= 0 || !consulta.datos || accion.ocupado}>
                    {accion.ocupado ? 'Registrando…' : 'Registrar pago'}
                  </Boton>
                )}
              </div>
            </>
          )}
        </Tarjeta>

        <div className={pagina.columna}>
          <Tarjeta tono="suave">
            <TarjetaEncabezado titulo="Un solo cobro, cuentas claras" />
            <p className={styles.explicacion}>
              Cada estado de cuenta se cancela completo en un solo pago, así ningún saldo queda a medias y sabes de un vistazo quién está al
              día. Si el cliente llega tarde, el total ya suma la mora de los días de atraso. Si entrega de más, Bizon te dice cuánto vuelto
              darle; ese dinero no se adelanta a cuotas futuras.
            </p>
          </Tarjeta>

          <Tarjeta>
            <TarjetaEncabezado titulo="Orden de aplicación del pago" descripcion="Bizon reparte cada pago en este orden, para que nada quede pendiente." />
            <ol className={styles.prelacion}>
              {PRELACION.map((concepto, indice) => (
                <li key={concepto}>
                  <span className={styles.prelacionNumero}>{indice + 1}</span>
                  {concepto}
                </li>
              ))}
            </ol>
          </Tarjeta>
        </div>
      </div>
    </Shell>
  )
}
