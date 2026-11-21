import { useState } from 'react'
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

/** El estado de cuenta más antiguo que el cliente todavía no paga. */
function estadoCuentaPendienteDe(clienteId: number) {
  return estadosCuentaDemo.find((candidato) => candidato.cliente_id === clienteId && candidato.estado !== 'PAGADO')
}

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
  const [resultado, setResultado] = useState<'registrado' | 'monto-distinto' | null>(null)

  if (clientesActivos.length === 0) {
    return (
      <Shell titulo="Registrar pago" subtitulo="El pago debe ser por el monto exacto de lo adeudado: no se aceptan pagos parciales.">
        <Aviso tono="info">Todavía no hay clientes activos. Regístralos primero en Clientes.</Aviso>
      </Shell>
    )
  }

  const cliente = clientesActivos.find((candidato) => candidato.id_cliente === clienteId) ?? clientesActivos[0]
  const estadoCuenta = estadoCuentaPendienteDe(cliente.id_cliente)
  const totalAPagar = estadoCuenta ? Number(estadoCuenta.total_pagar) : 0
  const tieneMora = estadoCuenta ? Number(estadoCuenta.total_interes_mora) > 0 : false

  function alRegistrar() {
    // se compara en céntimos para no depender de decimales de punto flotante
    const coincideConLoAdeudado = Math.round(Number(monto) * 100) === Math.round(totalAPagar * 100)
    setResultado(coincideConLoAdeudado ? 'registrado' : 'monto-distinto')
  }

  return (
    <Shell titulo="Registrar pago" subtitulo="El pago debe ser por el monto exacto de lo adeudado: no se aceptan pagos parciales.">
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
                setMonto('')
                setResultado(null)
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
                  <Insignia texto={ESTADO_CUENTA[estadoCuenta.estado].texto} tono={ESTADO_CUENTA[estadoCuenta.estado].tono} />
                </div>
                <ListaDatos>
                  <FilaDato etiqueta="Fecha de corte" valor={formatearFecha(estadoCuenta.fecha_corte)} />
                  <FilaDato etiqueta="Fecha de pago pactada" valor={formatearFecha(estadoCuenta.fecha_pago)} />
                  <FilaDato etiqueta="Capital" valor={formatearSoles(estadoCuenta.total_capital)} separada />
                  <FilaDato etiqueta="Interés compensatorio" valor={formatearSoles(estadoCuenta.total_interes_comp)} />
                  <FilaDato
                    etiqueta="Interés moratorio"
                    valor={formatearSoles(estadoCuenta.total_interes_mora)}
                    tono={tieneMora ? 'peligro' : undefined}
                  />
                  <FilaDato etiqueta="Total a pagar" valor={formatearSoles(estadoCuenta.total_pagar)} enfasis separada />
                </ListaDatos>
              </div>

              <div className={styles.bloque}>
                <Campo
                  etiqueta="Monto recibido (S/)"
                  ayuda="Debe coincidir exactamente con el total a pagar. Si el cliente paga después de la fecha pactada, la mora ya está incluida en el total."
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
                    placeholder={Number(estadoCuenta.total_pagar).toFixed(2)}
                    value={monto}
                    onChange={(evento) => {
                      setMonto(evento.target.value)
                      setResultado(null)
                    }}
                  />
                </Campo>
              </div>

              <div className={[styles.bloque, pagina.pila].join(' ')}>
                {resultado === 'monto-distinto' && (
                  <Aviso tono="peligro">
                    El monto no coincide con lo adeudado ({formatearSoles(totalAPagar)}). No se permiten pagos parciales: ingresa el monto
                    exacto.
                  </Aviso>
                )}

                {resultado === 'registrado' && (
                  <Aviso tono="exito" titulo="Pago registrado (demostración). Así se aplicó:">
                    <ol className={styles.aplicacion}>
                      <li>Interés moratorio: {formatearSoles(estadoCuenta.total_interes_mora)}</li>
                      <li>Interés compensatorio: {formatearSoles(estadoCuenta.total_interes_comp)}</li>
                      <li>Capital: {formatearSoles(estadoCuenta.total_capital)}</li>
                    </ol>
                  </Aviso>
                )}

                <Boton anchoCompleto onClick={alRegistrar} disabled={monto === '' || resultado === 'registrado'}>
                  Registrar pago
                </Boton>
              </div>
            </>
          )}
        </Tarjeta>

        <div className={pagina.columna}>
          <Tarjeta tono="suave">
            <TarjetaEncabezado titulo="¿Por qué el monto es exacto?" />
            <p className={styles.explicacion}>
              El enunciado del curso no permite pagos parciales de una deuda en su fecha de pago. La mora no nace de pagar una parte, sino de
              pagar tarde: si el cliente paga después de lo pactado, ese día debe cubrir lo adeudado completo más la mora acumulada.
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
