import { useEffect, useState } from 'react'
import { SIN_CONEXION, consultarExigible, procesarPago, type RespuestaPago } from '../../api/pagos'
import { Shell } from '../../components/layout/Shell'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { useDatos } from '../../contexts/datos'
import { estadosCuentaDemo, nombreCompleto } from '../../data/mock'
import { ESTADO_CUENTA } from '../../utils/etiquetas'
import { formatearFecha, formatearSoles } from '../../utils/formato'
import pagina from '../../styles/pagina.module.css'
import styles from './RegistrarPago.module.css'

/** El estado de cuenta más antiguo que el cliente todavía no paga (pagados: los cobrados en esta sesión). */
function estadoCuentaPendienteDe(clienteId: number, pagados: number[] = []) {
  return estadosCuentaDemo.find(
    (candidato) => candidato.cliente_id === clienteId && candidato.estado !== 'PAGADO' && !pagados.includes(candidato.id_estado_cuenta),
  )
}

/** La fecha de hoy en formato AAAA-MM-DD, en hora local. */
function hoyIso() {
  const hoy = new Date()
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`
}

const SUBTITULO = 'El pago debe cubrir todo lo adeudado: no se aceptan pagos parciales y el excedente se devuelve.'

/** Orden en que se aplica un pago (Anexo A del enunciado). */
const PRELACION = ['Interés moratorio', 'Interés compensatorio', 'Capital']

export function RegistrarPago() {
  // Los clientes salen de la lista compartida: los recién registrados también aparecen aquí.
  const { clientes } = useDatos()
  const clientesActivos = clientes.filter((candidato) => candidato.activo)

  // La pantalla abre en el primer cliente que tiene algo por pagar.
  const [clienteId, setClienteId] = useState(
    () => (clientesActivos.find((candidato) => estadoCuentaPendienteDe(candidato.id_cliente)) ?? clientesActivos[0])?.id_cliente ?? 0,
  )
  const [monto, setMonto] = useState('')
  const [fechaPago, setFechaPago] = useState(hoyIso)
  // Lo que el backend calcula para la fecha elegida (mora incluida) y su respuesta al registrar.
  const [exigible, setExigible] = useState<RespuestaPago | null>(null)
  const [resultado, setResultado] = useState<RespuestaPago | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  // Estados de cuenta cobrados en esta sesión; el último es el que se acaba de pagar.
  const [pagados, setPagados] = useState<number[]>([])

  const cliente = clientesActivos.find((candidato) => candidato.id_cliente === clienteId) ?? clientesActivos[0]
  // Mientras se muestra el resultado de un pago aceptado, se sigue viendo el estado de cuenta recién pagado.
  const yaCobrados = resultado?.aceptado ? pagados.slice(0, -1) : pagados
  const estadoCuenta = cliente ? estadoCuentaPendienteDe(cliente.id_cliente, yaCobrados) : undefined
  const idEstadoCuenta = estadoCuenta?.id_estado_cuenta
  const pagoAceptado = resultado?.aceptado === true

  // Cada vez que cambia el cliente o la fecha de pago, el backend recalcula la mora y el total.
  useEffect(() => {
    if (!estadoCuenta || !cliente || !fechaPago || pagoAceptado) return
    let vigente = true
    consultarExigible(estadoCuenta, cliente.condicion, fechaPago)
      .then((respuesta) => {
        if (!vigente) return
        setExigible(respuesta)
        setError(null)
      })
      .catch(() => {
        if (!vigente) return
        setExigible(null)
        setError(SIN_CONEXION)
      })
    return () => {
      vigente = false
    }
    // Solo depende de qué estado de cuenta se paga y en qué fecha.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idEstadoCuenta, fechaPago, pagoAceptado])

  if (clientesActivos.length === 0) {
    return (
      <Shell titulo="Registrar pago" subtitulo={SUBTITULO}>
        <Aviso tono="info">Todavía no hay clientes activos. Regístralos primero en Clientes.</Aviso>
      </Shell>
    )
  }

  // La mora y el total salen del backend; sin conexión se muestran los del estado de cuenta emitido.
  const interesMora = exigible?.interes_mora ?? estadoCuenta?.total_interes_mora ?? '0'
  const totalAPagar = exigible?.total_exigible ?? estadoCuenta?.total_pagar ?? '0'
  const tieneMora = Number(interesMora) > 0

  function reiniciar() {
    setMonto('')
    setResultado(null)
    setExigible(null)
  }

  async function alRegistrar() {
    if (!estadoCuenta) return
    setEnviando(true)
    try {
      const respuesta = await procesarPago(estadoCuenta, cliente.condicion, fechaPago, Number(monto).toFixed(2))
      setResultado(respuesta)
      setError(null)
      if (respuesta.aceptado) setPagados((actuales) => [...actuales, estadoCuenta.id_estado_cuenta])
    } catch {
      setError(SIN_CONEXION)
    } finally {
      setEnviando(false)
    }
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
              onChange={(evento) => {
                setClienteId(Number(evento.target.value))
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

          {!estadoCuenta ? (
            <div className={styles.bloque}>
              <Aviso tono="info" titulo={`${nombreCompleto(cliente)} no tiene nada por pagar`}>
                Los cobros aparecen aquí cuando se emite su estado de cuenta, en la fecha de corte posterior a una compra. Un cliente recién
                registrado todavía no tiene compras.
              </Aviso>
            </div>
          ) : (
            <>
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
                  <FilaDato etiqueta="Fecha de corte" valor={formatearFecha(estadoCuenta.fecha_corte)} />
                  <FilaDato etiqueta="Fecha de pago pactada" valor={formatearFecha(estadoCuenta.fecha_pago)} />
                  <FilaDato
                    etiqueta="Días de mora"
                    valor={exigible ? String(exigible.dias_mora) : '—'}
                    tono={tieneMora ? 'peligro' : undefined}
                  />
                  <FilaDato etiqueta="Capital" valor={formatearSoles(estadoCuenta.total_capital)} separada />
                  <FilaDato etiqueta="Interés compensatorio" valor={formatearSoles(estadoCuenta.total_interes_comp)} />
                  <FilaDato etiqueta="Interés moratorio" valor={formatearSoles(interesMora)} tono={tieneMora ? 'peligro' : undefined} />
                  <FilaDato etiqueta="Total a pagar" valor={formatearSoles(totalAPagar)} enfasis separada />
                </ListaDatos>
              </div>

              <div className={styles.bloque}>
                <Campo
                  etiqueta="Fecha en que paga"
                  ayuda="Si es posterior a la fecha de pago pactada, el sistema calcula los días de mora y suma el interés moratorio al total."
                  obligatorio
                  htmlFor="fecha_pago"
                >
                  <input
                    id="fecha_pago"
                    type="date"
                    className="campo-entrada"
                    value={fechaPago}
                    disabled={pagoAceptado}
                    onChange={(evento) => {
                      setFechaPago(evento.target.value)
                      setResultado(null)
                    }}
                  />
                </Campo>
              </div>

              <div className={styles.bloque}>
                <Campo
                  etiqueta="Monto recibido (S/)"
                  ayuda="Debe cubrir el total a pagar, que ya incluye la mora. Si el cliente entrega más, el sistema indica cuánto devolverle."
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
                    placeholder={Number(totalAPagar).toFixed(2)}
                    value={monto}
                    disabled={pagoAceptado}
                    onChange={(evento) => {
                      setMonto(evento.target.value)
                      setResultado(null)
                    }}
                  />
                </Campo>
              </div>

              <div className={[styles.bloque, pagina.pila].join(' ')}>
                {error && <Aviso tono="peligro">{error}</Aviso>}

                {resultado && !resultado.aceptado && (
                  <Aviso tono="peligro" titulo="Pago rechazado">
                    El monto no cubre lo adeudado ({formatearSoles(resultado.total_exigible)}). No se permiten pagos parciales: faltan{' '}
                    {formatearSoles(Number(resultado.total_exigible) - Number(monto))}.
                  </Aviso>
                )}

                {resultado && resultado.aceptado && (
                  <Aviso tono="exito" titulo="Pago registrado. Así se aplicó:">
                    <ol className={styles.aplicacion}>
                      <li>Interés moratorio: {formatearSoles(resultado.aplicado_mora)}</li>
                      <li>Interés compensatorio: {formatearSoles(resultado.aplicado_interes_comp)}</li>
                      <li>Capital: {formatearSoles(resultado.aplicado_capital)}</li>
                    </ol>
                    {Number(resultado.excedente_devuelto) > 0 && (
                      <p>Devuelve al cliente {formatearSoles(resultado.excedente_devuelto)} de excedente.</p>
                    )}
                  </Aviso>
                )}

                {pagoAceptado ? (
                  <Boton anchoCompleto onClick={reiniciar}>
                    Registrar otro pago
                  </Boton>
                ) : (
                  <Boton anchoCompleto onClick={alRegistrar} disabled={monto === '' || Number(monto) <= 0 || enviando}>
                    {enviando ? 'Registrando…' : 'Registrar pago'}
                  </Boton>
                )}
              </div>
            </>
          )}
        </Tarjeta>

        <div className={pagina.columna}>
          <Tarjeta tono="suave">
            <TarjetaEncabezado titulo="¿Por qué no hay pagos parciales?" />
            <p className={styles.explicacion}>
              El enunciado del curso no permite pagos parciales de una deuda en su fecha de pago. La mora no nace de pagar una parte, sino de
              pagar tarde: si el cliente paga después de lo pactado, ese día debe cubrir lo adeudado completo más la mora acumulada. Si
              entrega de más, el excedente se le devuelve: no se adelantan cuotas futuras.
            </p>
          </Tarjeta>

          <Tarjeta>
            <TarjetaEncabezado titulo="Orden de aplicación del pago" descripcion="Prelación exigida por el Anexo A." />
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
