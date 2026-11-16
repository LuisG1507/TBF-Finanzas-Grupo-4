import { useState } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Icono } from '../../components/ui/Icono'
import { FilaDato, ListaDatos } from '../../components/ui/ListaDatos'
import { Medidor } from '../../components/ui/Medidor'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { useDatos } from '../../contexts/datos'
import { codigoUnidad, nombreCompleto, posicionDe } from '../../data/mock'
import type { ModalidadCompra } from '../../types/dominio'
import { formatearPorcentaje, formatearSoles, plural, sumarMontos } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import pagina from '../../styles/pagina.module.css'
import styles from './NuevaCompra.module.css'

interface ItemCarrito {
  productoId: number
  cantidad: number
}

/** Los productos que se venden por unidad no admiten fracciones; los que van por kilo o litro, sí. */
function pasoDeCantidad(unidadId: number): number {
  return codigoUnidad(unidadId) === 'UND' ? 1 : 0.1
}

export function NuevaCompra() {
  // Clientes y productos salen de la lista compartida: los recién registrados aparecen aquí (y van primero).
  const { clientes, productos } = useDatos()
  const clientesActivos = clientes.filter((candidato) => candidato.activo)
  const productosActivos = productos.filter((candidato) => candidato.activo)

  const [clienteId, setClienteId] = useState(() => clientesActivos[0]?.id_cliente ?? 0)
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [productoAAgregar, setProductoAAgregar] = useState(() => productosActivos[0]?.id_producto ?? 0)
  const [cantidadAAgregar, setCantidadAAgregar] = useState('1')
  const [modalidadElegida, setModalidadElegida] = useState<ModalidadCompra>('FIN_DE_MES')
  const [numCuotas, setNumCuotas] = useState(2)
  const [registrada, setRegistrada] = useState(false)

  if (clientesActivos.length === 0 || productosActivos.length === 0) {
    return (
      <Shell titulo="Nueva compra" subtitulo="Registra una venta a crédito, con uno o varios productos.">
        <Aviso tono="info">
          Para registrar una compra necesitas al menos un cliente activo y un producto activo. Regístralos primero en Clientes y en
          Productos.
        </Aviso>
      </Shell>
    )
  }

  const cliente = clientesActivos.find((candidato) => candidato.id_cliente === clienteId) ?? clientesActivos[0]
  const { condicion } = cliente
  const productoElegido = productosActivos.find((producto) => producto.id_producto === productoAAgregar) ?? productosActivos[0]

  const lineas = carrito.flatMap((item) => {
    const producto = productos.find((candidato) => candidato.id_producto === item.productoId)
    if (!producto) return []
    // el subtotal se redondea a céntimos, como lo guardará el backend
    const subtotal = Math.round(Number(producto.precio_lista) * item.cantidad * 100) / 100
    return [{ producto, cantidad: item.cantidad, subtotal }]
  })
  const total = sumarMontos(lineas.map((linea) => linea.subtotal))

  // La modalidad se aplica a toda la compra: todos los productos deben admitirla.
  const admiteFinDeMes = lineas.every((linea) => linea.producto.permite_fin_de_mes)
  const admiteCuotas = lineas.every((linea) => linea.producto.permite_cuotas)
  const modalidad: ModalidadCompra | null =
    modalidadElegida === 'FIN_DE_MES'
      ? admiteFinDeMes
        ? 'FIN_DE_MES'
        : admiteCuotas
          ? 'CUOTAS'
          : null
      : admiteCuotas
        ? 'CUOTAS'
        : admiteFinDeMes
          ? 'FIN_DE_MES'
          : null

  // El límite se compara contra el saldo de capital pendiente (sin intereses).
  const limite = Number(condicion.limite_credito)
  // Un cliente recién registrado todavía no tiene compras: su saldo es cero.
  const saldoPendiente = Number(posicionDe(cliente.id_cliente)?.saldo_capital ?? 0)
  const disponible = sumarMontos([limite, -saldoPendiente])
  const excedeLimite = total > disponible
  const usoConEstaCompra = sumarMontos([saldoPendiente, total])
  const cuotasValidas = modalidad !== 'CUOTAS' || (numCuotas >= 1 && numCuotas <= condicion.max_meses)
  const cantidadValida = Number(cantidadAAgregar) > 0

  function agregarProducto() {
    const cantidad = Number(cantidadAAgregar)
    if (!(cantidad > 0)) return
    setRegistrada(false)
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
    setCarrito((actual) => actual.filter((item) => item.productoId !== productoId))
  }

  function registrarCompra() {
    setRegistrada(true)
    setCarrito([])
  }

  return (
    <Shell titulo="Nueva compra" subtitulo="Registra una venta a crédito, con uno o varios productos.">
      <div className={pagina.dosColumnas}>
        <div className={pagina.columna}>
          <Tarjeta>
            <TarjetaEncabezado titulo="Cliente" />
            <Campo etiqueta="¿Quién compra?" ayuda="Solo aparecen los clientes con crédito activo en esta tienda." htmlFor="cliente">
              <select
                id="cliente"
                className="campo-entrada"
                value={cliente.id_cliente}
                onChange={(evento) => {
                  setClienteId(Number(evento.target.value))
                  setCarrito([])
                  setRegistrada(false)
                }}
              >
                {clientesActivos.map((opcion) => (
                  <option key={opcion.id_cliente} value={opcion.id_cliente}>
                    {nombreCompleto(opcion)}
                  </option>
                ))}
              </select>
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
                  onChange={(evento) => setProductoAAgregar(Number(evento.target.value))}
                >
                  {productosActivos.map((producto) => (
                    <option key={producto.id_producto} value={producto.id_producto}>
                      {producto.nombre} — {formatearSoles(producto.precio_lista)}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo etiqueta={`Cantidad (${codigoUnidad(productoElegido.unidad_id)})`} ayuda="Mayor que cero." htmlFor="cantidad">
                <input
                  id="cantidad"
                  type="number"
                  min={pasoDeCantidad(productoElegido.unidad_id)}
                  step={pasoDeCantidad(productoElegido.unidad_id)}
                  inputMode="decimal"
                  className="campo-entrada"
                  value={cantidadAAgregar}
                  onChange={(evento) => setCantidadAAgregar(evento.target.value)}
                />
              </Campo>
              <Boton variante="secundario" icono="mas" className={styles.botonAgregar} onClick={agregarProducto} disabled={!cantidadValida}>
                Agregar
              </Boton>
            </div>

            {lineas.length === 0 ? (
              <p className={tabla.vacio}>Todavía no agregaste ningún producto.</p>
            ) : (
              <ul className={styles.carrito}>
                {lineas.map((linea) => (
                  <li key={linea.producto.id_producto} className={styles.linea}>
                    <div className={styles.lineaTexto}>
                      <p className={styles.lineaNombre}>{linea.producto.nombre}</p>
                      <p className={styles.lineaDetalle}>
                        {linea.cantidad} {codigoUnidad(linea.producto.unidad_id)} × {formatearSoles(linea.producto.precio_lista)}
                      </p>
                    </div>
                    <span className={styles.lineaSubtotal}>{formatearSoles(linea.subtotal)}</span>
                    <button
                      type="button"
                      className={styles.quitar}
                      onClick={() => quitarProducto(linea.producto.id_producto)}
                      aria-label={`Quitar ${linea.producto.nombre}`}
                      title="Quitar"
                    >
                      <Icono nombre="cerrar" tamano={15} grosor={2} />
                    </button>
                  </li>
                ))}
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
                    disabled={!admiteFinDeMes}
                    onChange={() => setModalidadElegida('FIN_DE_MES')}
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
                    disabled={!admiteCuotas}
                    onChange={() => setModalidadElegida('CUOTAS')}
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
                      onChange={(evento) => setNumCuotas(Number(evento.target.value))}
                    />
                  </Campo>
                </div>
              )}
            </Tarjeta>
          )}
        </div>

        <Tarjeta className={pagina.pegajosa}>
          <TarjetaEncabezado titulo="Resumen del crédito" descripcion={nombreCompleto(cliente)} />
          <ListaDatos>
            <FilaDato etiqueta="Límite de crédito" valor={formatearSoles(limite)} />
            <FilaDato etiqueta="Saldo pendiente" valor={formatearSoles(saldoPendiente)} />
            <FilaDato etiqueta="Disponible" valor={formatearSoles(disponible)} />
            <FilaDato etiqueta="Total de esta compra" valor={formatearSoles(total)} enfasis separada />
          </ListaDatos>

          <div className={styles.uso}>
            <Medidor
              etiqueta="Uso del límite de crédito con esta compra"
              valor={usoConEstaCompra}
              maximo={limite}
              textoValor={`${formatearSoles(usoConEstaCompra)} de ${formatearSoles(limite)}`}
              tono={excedeLimite ? 'peligro' : 'acento'}
            />
            <p className={pagina.nota}>
              Con esta compra usaría {formatearPorcentaje(limite > 0 ? usoConEstaCompra / limite : 0)} de su límite.
            </p>
          </div>

          <div className={pagina.pila}>
            {excedeLimite && (
              <Aviso tono="peligro">
                Esta compra supera el crédito disponible del cliente por {formatearSoles(sumarMontos([total, -disponible]))}. No se puede
                registrar por encima de su límite.
              </Aviso>
            )}

            {registrada && (
              <Aviso tono="exito" titulo="Compra registrada (demostración)">
                Cuando esta pantalla se conecte al backend, aquí se generará el cronograma de pagos.
              </Aviso>
            )}

            <Boton
              anchoCompleto
              disabled={lineas.length === 0 || excedeLimite || modalidad === null || !cuotasValidas}
              onClick={registrarCompra}
            >
              Registrar compra
            </Boton>
          </div>
        </Tarjeta>
      </div>
    </Shell>
  )
}
