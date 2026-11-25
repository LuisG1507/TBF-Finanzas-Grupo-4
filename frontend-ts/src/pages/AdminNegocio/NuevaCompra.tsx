import { useState } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Icono } from '../../components/ui/Icono'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Medidor } from '../../components/ui/Medidor'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { pedir } from '../../api/cliente'
import { useAccion, useConsulta, useLista } from '../../api/consultas'
import { DetalleCompra } from '../../components/negocio/DetalleCompra'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import { nombreCompleto } from '../../utils/texto'
import type { Cliente, Compra, CreditoDisponible, ModalidadCompra, Producto } from '../../types/dominio'
import { formatearMonto, formatearPorcentaje, formatearSoles, plural, sumarMontos } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import pagina from '../../styles/pagina.module.css'
import styles from './NuevaCompra.module.css'

interface ItemCarrito {
  productoId: number
  cantidad: number
}

/** Los productos que se venden por unidad no admiten fracciones; los que van por kilo o litro, sí. */
function pasoDeCantidad(codigo: string): number {
  return codigo === 'UND' ? 1 : 0.001
}

export function NuevaCompra() {
  const consultaClientes = useLista<Cliente>('/clientes?activo=true')
  const consultaProductos = useLista<Producto>('/productos?activo=true')
  const clientesActivos = (consultaClientes.datos ?? []).filter((cliente) => cliente.condicion !== null)
  const productos = consultaProductos.datos ?? []
  const [clienteId, setClienteId] = useState(0)
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [productoAAgregar, setProductoAAgregar] = useState(0)
  const [cantidadAAgregar, setCantidadAAgregar] = useState('1')
  const [modalidadElegida, setModalidadElegida] = useState<ModalidadCompra>('FIN_DE_MES')
  const [numCuotas, setNumCuotas] = useState(2)
  const [fechaCompra, setFechaCompra] = useState('')
  const [simulacion, setSimulacion] = useState<{ clave: string; compra: Compra } | null>(null)
  const [registrada, setRegistrada] = useState<Compra | null>(null)
  const accion = useAccion()

  const cliente = clientesActivos.find((candidato) => candidato.id_cliente === clienteId) ?? clientesActivos[0]
  const condicion = cliente?.condicion
  const productoElegido = productos.find((producto) => producto.id_producto === productoAAgregar) ?? productos[0]
  const credito = useConsulta<CreditoDisponible>(cliente ? '/clientes/' + cliente.id_cliente + '/credito-disponible' : null)
  if (!condicion || !productoElegido) {
    return (
      <Shell titulo="Nueva compra" subtitulo="Registra una venta a crédito, con uno o varios productos.">
        <EstadoConsulta {...consultaClientes} />
        <EstadoConsulta {...consultaProductos} />
        {consultaClientes.datos && consultaProductos.datos && (
          <Aviso tono="info">Para registrar una compra necesitas un cliente con crédito activo y un producto activo.</Aviso>
        )}
      </Shell>
    )
  }

  const lineas = carrito.flatMap((item) => {
    const producto = productos.find((candidato) => candidato.id_producto === item.productoId)
    return producto ? [{ producto, cantidad: item.cantidad }] : []
  })
  const admiteFinDeMes = lineas.every((linea) => linea.producto.permite_fin_de_mes)
  const admiteCuotas = lineas.every((linea) => linea.producto.permite_cuotas)
  const modalidades: ModalidadCompra[] = []
  if (admiteFinDeMes) modalidades.push('FIN_DE_MES')
  if (admiteCuotas) modalidades.push('CUOTAS')
  const modalidad = modalidades.includes(modalidadElegida) ? modalidadElegida : (modalidades[0] ?? null)
  const cuerpo = {
    cliente_id: cliente.id_cliente,
    modalidad,
    num_cuotas: modalidad === 'CUOTAS' ? numCuotas : null,
    items: carrito.map((item) => ({ producto_id: item.productoId, cantidad: String(item.cantidad) })),
    fecha_hora_compra: fechaCompra || null,
  }
  const clave = JSON.stringify(cuerpo)
  const previa = simulacion?.clave === clave ? simulacion.compra : null
  const moneda = previa?.moneda.codigo_iso ?? condicion.moneda.codigo_iso
  const creditoActual = previa?.credito ?? credito.datos
  const limite = Number(creditoActual?.limite_credito ?? condicion.limite_credito)
  const saldoPendiente = creditoActual?.capital_pendiente
  const disponible = creditoActual?.credito_disponible
  const total = previa?.monto_total
  const excedeLimite = Boolean(previa?.credito?.excede_limite)
  const usoConEstaCompra = sumarMontos([saldoPendiente ?? 0, total ?? 0])
  const cuotasValidas = modalidad !== 'CUOTAS' || (Number.isInteger(numCuotas) && numCuotas >= 1 && numCuotas <= condicion.max_meses)
  const cantidad = Number(cantidadAAgregar)
  const paso = pasoDeCantidad(productoElegido.unidad.codigo)
  const cantidadValida = cantidad > 0 && Math.abs(cantidad / paso - Math.round(cantidad / paso)) < 0.000001

  function agregarProducto() {
    if (!cantidadValida) return
    setRegistrada(null)
    setSimulacion(null)
    accion.limpiarError()
    const productoId = productoElegido.id_producto
    setCarrito((actual) =>
      actual.some((item) => item.productoId === productoId)
        ? actual.map((item) =>
            item.productoId === productoId ? { ...item, cantidad: Math.round((item.cantidad + cantidad) * 1000) / 1000 } : item,
          )
        : [...actual, { productoId, cantidad }],
    )
  }

  function quitarProducto(productoId: number) {
    setSimulacion(null)
    setCarrito((actual) => actual.filter((item) => item.productoId !== productoId))
  }

  function simularCompra() {
    void accion.ejecutar(async () => {
      setSimulacion(null)
      const compra = await pedir<Compra>('/compras/simular', { method: 'POST', cuerpo })
      setSimulacion({ clave, compra })
    })
  }

  function registrarCompra() {
    if (!previa || excedeLimite) return
    void accion.ejecutar(async () => {
      const compra = await pedir<Compra>('/compras', {
        method: 'POST', cuerpo: { ...cuerpo, fecha_hora_compra: previa.fecha_hora_compra },
      })
      setRegistrada(compra)
      setSimulacion(null)
      setCarrito([])
      credito.recargar()
    })
  }

  return (
    <Shell titulo="Nueva compra" subtitulo="Registra una venta a crédito, con uno o varios productos.">
      <EstadoConsulta error={accion.error} />
      <div className={pagina.dosColumnas}>
        <div className={pagina.columna}>
          <Tarjeta>
            <TarjetaEncabezado titulo="Cliente" />
            <Campo etiqueta="¿Quién compra?" ayuda="Solo aparecen los clientes con crédito activo en esta tienda." htmlFor="cliente">
              <select
                id="cliente"
                className="campo-entrada"
                value={cliente.id_cliente}
                disabled={accion.ocupado}
                onChange={(evento) => {
                  setClienteId(Number(evento.target.value))
                  setCarrito([])
                  setRegistrada(null)
                  setSimulacion(null)
                  accion.limpiarError()
                }}
              >
                {clientesActivos.map((opcion) => (
                  <option key={opcion.id_cliente} value={opcion.id_cliente}>
                    {nombreCompleto(opcion)}
                  </option>
                ))}
              </select>
            </Campo>
            <Campo etiqueta="Fecha y hora de compra" ayuda="Hora de Lima. Si la dejas vacía se usa el momento de la simulación." htmlFor="fecha-compra">
              <input id="fecha-compra" type="datetime-local" className="campo-entrada" value={fechaCompra} disabled={accion.ocupado}
                onChange={(evento) => { setFechaCompra(evento.target.value); setSimulacion(null) }} />
            </Campo>
            <ul className={styles.condiciones}>
              <li>
                <Icono nombre="calendario" tamano={15} /> Corte el día {condicion.dia_corte}
              </li>
              <li>
                <Icono nombre="billete" tamano={15} /> Paga el día {condicion.dia_pago}
              </li>
              <li>
                <Icono nombre="documento" tamano={15} /> Hasta {plural(condicion.max_meses, 'cuota', 'cuotas')}
              </li>
            </ul>
          </Tarjeta>

          <Tarjeta>
            <TarjetaEncabezado titulo="Productos de la compra" />
            <div className={styles.agregar}>
              <Campo etiqueta="Producto" ayuda="Se cobra al precio de lista (el de crédito)." htmlFor="producto">
                <select
                  id="producto"
                  className="campo-entrada"
                  value={productoElegido.id_producto}
                  disabled={accion.ocupado}
                  onChange={(evento) => setProductoAAgregar(Number(evento.target.value))}
                >
                  {productos.map((producto) => (
                    <option key={producto.id_producto} value={producto.id_producto}>
                      {producto.nombre} — {formatearSoles(producto.precio_lista)}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo etiqueta={`Cantidad (${productoElegido.unidad.codigo})`} ayuda="Mayor que cero." htmlFor="cantidad">
                <input
                  id="cantidad"
                  type="number"
                  min={paso}
                  step={paso}
                  inputMode="decimal"
                  className="campo-entrada"
                  value={cantidadAAgregar}
                  disabled={accion.ocupado}
                  onChange={(evento) => setCantidadAAgregar(evento.target.value)}
                />
              </Campo>
              <Boton variante="secundario" icono="mas" className={styles.botonAgregar} onClick={agregarProducto} disabled={!cantidadValida || accion.ocupado}>
                Agregar
              </Boton>
            </div>

            {lineas.length === 0 ? (
              <p className={tabla.vacio}>Todavía no agregaste ningún producto.</p>
            ) : (
              <ul className={styles.carrito}>
                {lineas.map((linea) => {
                  const item = previa?.items.find((fila) => fila.producto_id === linea.producto.id_producto)
                  return (
                    <li key={linea.producto.id_producto} className={styles.linea}>
                      <div className={styles.lineaTexto}>
                        <p className={styles.lineaNombre}>{linea.producto.nombre}</p>
                        <p className={styles.lineaDetalle}>
                          {linea.cantidad} {linea.producto.unidad.codigo} · {item ? formatearMonto(item.precio_unitario, moneda) : formatearSoles(linea.producto.precio_lista)}
                        </p>
                      </div>
                      <span className={styles.lineaSubtotal}>{item ? formatearMonto(item.subtotal, moneda) : '—'}</span>
                      <button
                        type="button"
                        className={styles.quitar}
                        disabled={accion.ocupado}
                        onClick={() => quitarProducto(linea.producto.id_producto)}
                        aria-label={`Quitar ${linea.producto.nombre}`}
                        title="Quitar"
                      >
                        <Icono nombre="cerrar" tamano={15} grosor={2} />
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </Tarjeta>

          {lineas.length > 0 && (
            <Tarjeta>
              <TarjetaEncabezado
                titulo="Forma de pago"
                descripcion="Se aplica a toda la compra: todos los productos deben admitir la modalidad elegida."
              />
              <div className={styles.modalidades} role="radiogroup" aria-label="Forma de pago">
                <label className={styles.modalidad}>
                  <input
                    type="radio"
                    name="modalidad"
                    checked={modalidad === 'FIN_DE_MES'}
                    disabled={!admiteFinDeMes || accion.ocupado}
                    onChange={() => { setModalidadElegida('FIN_DE_MES'); setSimulacion(null) }}
                  />
                  <span>
                    <span className={styles.modalidadTitulo}>Un solo pago a fin de mes</span>
                    <span className={styles.modalidadTexto}>Se cobra completo en su próxima fecha de pago.</span>
                  </span>
                </label>
                <label className={styles.modalidad}>
                  <input
                    type="radio"
                    name="modalidad"
                    checked={modalidad === 'CUOTAS'}
                    disabled={!admiteCuotas || accion.ocupado}
                    onChange={() => { setModalidadElegida('CUOTAS'); setSimulacion(null) }}
                  />
                  <span>
                    <span className={styles.modalidadTitulo}>En cuotas mensuales</span>
                    <span className={styles.modalidadTexto}>Cuotas iguales por el método francés.</span>
                  </span>
                </label>
              </div>

              {modalidad === null && (
                <Aviso tono="alerta">
                  Estos productos no comparten una forma de pago: unos solo van a fin de mes y otros solo en cuotas. Regístralos en dos compras.
                </Aviso>
              )}

              {modalidad === 'CUOTAS' && (
                <div className={styles.cuotas}>
                  <Campo
                    etiqueta="Número de cuotas"
                    ayuda={`De 1 a ${condicion.max_meses}: es el máximo pactado con este cliente.`}
                    error={cuotasValidas ? undefined : `Debe estar entre 1 y ${condicion.max_meses}.`}
                    htmlFor="num_cuotas"
                  >
                    <input
                      id="num_cuotas"
                      type="number"
                      min={1}
                      max={condicion.max_meses}
                      step={1}
                      inputMode="numeric"
                      className="campo-entrada"
                      value={numCuotas}
                      disabled={accion.ocupado}
                      onChange={(evento) => { setNumCuotas(Number(evento.target.value)); setSimulacion(null) }}
                    />
                  </Campo>
                </div>
              )}
            </Tarjeta>
          )}
        </div>

        <Tarjeta className={pagina.pegajosa}>
          <TarjetaEncabezado titulo="Resumen del crédito" descripcion={nombreCompleto(cliente)} />
          <EstadoConsulta {...credito} />
          <ListaDatos>
            <FilaDato etiqueta="Límite de crédito" valor={formatearMonto(limite, moneda)} />
            <FilaDato etiqueta="Saldo pendiente" valor={saldoPendiente ? formatearMonto(saldoPendiente, moneda) : '—'} />
            <FilaDato etiqueta="Disponible" valor={disponible ? formatearMonto(disponible, moneda) : '—'} />
            <FilaDato etiqueta="Total de esta compra" valor={total ? formatearMonto(total, moneda) : '—'} enfasis separada />
          </ListaDatos>

          {creditoActual && <div className={styles.uso}>
            <Medidor
              etiqueta="Uso del límite de crédito con esta compra"
              valor={usoConEstaCompra}
              maximo={limite}
              textoValor={`${formatearMonto(usoConEstaCompra, moneda)} de ${formatearMonto(limite, moneda)}`}
              tono={excedeLimite ? 'peligro' : 'acento'}
            />
            <p className={pagina.nota}>
              {previa ? 'Con esta compra usaría ' : 'Actualmente usa '}{formatearPorcentaje(limite > 0 ? usoConEstaCompra / limite : 0)} de su límite.
              {previa && ' Es una proyección. Bizon vuelve a verificar el crédito disponible al registrar.'}
            </p>
          </div>}

          <div className={pagina.pila}>
            {excedeLimite && (
              <Aviso tono="peligro">
                Esta compra supera el crédito disponible del cliente.
              </Aviso>
            )}

            {registrada && <Aviso tono="exito" titulo="Compra registrada">Compra n.° {registrada.id_compra}.</Aviso>}
            <Boton anchoCompleto variante={previa ? 'secundario' : 'primario'}
              disabled={lineas.length === 0 || modalidad === null || !cuotasValidas || accion.ocupado} onClick={simularCompra}>
              {accion.ocupado && !previa ? 'Simulando…' : previa ? 'Volver a simular' : 'Simular compra'}
            </Boton>
            {previa && <Boton anchoCompleto disabled={excedeLimite || accion.ocupado} onClick={registrarCompra}>
              {accion.ocupado ? 'Guardando…' : 'Registrar compra'}
            </Boton>}
          </div>
        </Tarjeta>
      </div>
      {previa ? <ResultadoCompra compra={previa} /> : registrada && <ResultadoCompra compra={registrada} />}
    </Shell>
  )
}

function ResultadoCompra({ compra }: { compra: Compra }) {
  return (
    <Tarjeta>
      <TarjetaEncabezado titulo={compra.cronograma.length ? 'Cronograma de pagos' : 'Pago a fin de mes'} />
      <DetalleCompra compra={compra} />
    </Tarjeta>
  )
}
