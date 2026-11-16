import { useCallback, useState, type FormEvent } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Boton } from '../../components/ui/Boton'
import { Buscador } from '../../components/ui/Buscador'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { Modal } from '../../components/ui/Modal'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { siguienteId, useDatos } from '../../contexts/datos'
import { codigoUnidad, marcasDemo, nombreMarca, proveedoresDemo, unidadesDemo } from '../../data/mock'
import type { Producto } from '../../types/dominio'
import { formatearSoles, plural } from '../../utils/formato'
import { coincide } from '../../utils/texto'
import tabla from '../../components/ui/Tabla.module.css'
import formulario from '../../styles/formulario.module.css'
import pagina from '../../styles/pagina.module.css'

export function Productos() {
  // La lista es compartida: un producto nuevo aparece también al registrar una compra.
  const { productos, agregarProducto } = useDatos()
  const [modalAbierto, setModalAbierto] = useState(false)
  const [consulta, setConsulta] = useState('')
  const cerrarModal = useCallback(() => setModalAbierto(false), [])

  const activos = productos.filter((producto) => producto.activo).length
  const visibles = productos.filter((producto) =>
    coincide(consulta, producto.nombre, producto.codigo, nombreMarca(producto.marca_id)),
  )

  function alCrearProducto(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    const nuevo: Producto = {
      id_producto: siguienteId(productos.map((producto) => producto.id_producto)),
      codigo: String(datos.get('codigo')),
      nombre: String(datos.get('nombre')),
      descripcion: String(datos.get('descripcion') || '') || undefined,
      proveedor_id: datos.get('proveedor_id') ? Number(datos.get('proveedor_id')) : undefined,
      marca_id: datos.get('marca_id') ? Number(datos.get('marca_id')) : undefined,
      unidad_id: Number(datos.get('unidad_id')),
      precio_contado: Number(datos.get('precio_contado')).toFixed(2),
      precio_lista: Number(datos.get('precio_lista')).toFixed(2),
      permite_fin_de_mes: datos.get('permite_fin_de_mes') === 'on',
      permite_cuotas: datos.get('permite_cuotas') === 'on',
      activo: true,
    }
    agregarProducto(nuevo)
    setModalAbierto(false)
  }

  return (
    <Shell
      titulo="Productos"
      subtitulo="Lo que tu tienda ofrece a crédito, con su precio al contado y su precio de lista."
      acciones={
        <Boton icono="mas" onClick={() => setModalAbierto(true)}>
          Nuevo producto
        </Boton>
      }
    >
      <Tarjeta relleno="ninguno">
        <div className={pagina.barraTabla}>
          <p className={pagina.barraTablaTexto}>
            <strong>{plural(productos.length, 'producto', 'productos')}</strong> · {plural(activos, 'activo', 'activos')}
          </p>
          <Buscador valor={consulta} onCambiar={setConsulta} etiqueta="Buscar por nombre, código o marca" />
        </div>
        <div className={tabla.envoltura}>
          <table className={tabla.tabla}>
            <colgroup>
              <col style={{ width: '30%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '20%' }} />
              <col style={{ width: '13%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Unidad</th>
                <th className={tabla.numerica}>Precio contado</th>
                <th className={tabla.numerica}>Precio de lista</th>
                <th>Se vende</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((producto) => {
                const marca = nombreMarca(producto.marca_id)
                return (
                  <tr key={producto.id_producto}>
                    <td>
                      <div className={tabla.fuerte}>{producto.nombre}</div>
                      <div className={tabla.celdaSecundaria}>
                        {producto.codigo}
                        {marca ? ` · ${marca}` : ''}
                      </div>
                    </td>
                    <td>{codigoUnidad(producto.unidad_id)}</td>
                    <td className={tabla.numerica}>{formatearSoles(producto.precio_contado)}</td>
                    <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(producto.precio_lista)}</td>
                    <td>
                      <div className={tabla.grupoInsignias}>
                        {producto.permite_fin_de_mes && <Insignia texto="Fin de mes" />}
                        {producto.permite_cuotas && <Insignia texto="Cuotas" />}
                      </div>
                    </td>
                    <td>
                      <Insignia texto={producto.activo ? 'Activo' : 'Dado de baja'} tono={producto.activo ? 'exito' : 'neutro'} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {visibles.length === 0 && <p className={tabla.vacio}>Ningún producto coincide con «{consulta}».</p>}
      </Tarjeta>

      {modalAbierto && (
        <Modal titulo="Nuevo producto" descripcion="Aparecerá de inmediato al registrar una compra." onCerrar={cerrarModal} ancho={660}>
          <form className={formulario.formulario} onSubmit={alCrearProducto}>
            <div className={formulario.seccion}>
              <div className={formulario.rejilla3}>
                <Campo etiqueta="Código" ayuda="Código interno para ubicarlo rápido, por ejemplo P-007." obligatorio htmlFor="codigo">
                  <input id="codigo" name="codigo" className="campo-entrada" required />
                </Campo>
                <div className={formulario.dosColumnas}>
                  <Campo etiqueta="Nombre" ayuda="Como aparecerá en el catálogo y en el estado de cuenta." obligatorio htmlFor="nombre">
                    <input id="nombre" name="nombre" className="campo-entrada" required />
                  </Campo>
                </div>
              </div>

              <Campo etiqueta="Descripción" ayuda="Opcional. Detalles que ayuden a diferenciarlo de otros similares." htmlFor="descripcion">
                <textarea id="descripcion" name="descripcion" className="campo-entrada" rows={2} />
              </Campo>

              <div className={formulario.rejilla3}>
                <Campo etiqueta="Proveedor" ayuda="Opcional, si lo compras a un proveedor fijo." htmlFor="proveedor_id">
                  <select id="proveedor_id" name="proveedor_id" className="campo-entrada" defaultValue="">
                    <option value="">Sin proveedor</option>
                    {proveedoresDemo.map((proveedor) => (
                      <option key={proveedor.id_proveedor} value={proveedor.id_proveedor}>
                        {proveedor.razon_social}
                      </option>
                    ))}
                  </select>
                </Campo>
                <Campo etiqueta="Marca" ayuda="Opcional; no aplica a servicios." htmlFor="marca_id">
                  <select id="marca_id" name="marca_id" className="campo-entrada" defaultValue="">
                    <option value="">Sin marca</option>
                    {marcasDemo.map((marca) => (
                      <option key={marca.id_marca} value={marca.id_marca}>
                        {marca.nombre}
                      </option>
                    ))}
                  </select>
                </Campo>
                <Campo etiqueta="Unidad de medida" ayuda="Cómo se vende: por unidad, kilo o litro." obligatorio htmlFor="unidad_id">
                  <select id="unidad_id" name="unidad_id" className="campo-entrada" required defaultValue="">
                    <option value="" disabled>
                      Selecciona
                    </option>
                    {unidadesDemo.map((unidad) => (
                      <option key={unidad.id_unidad} value={unidad.id_unidad}>
                        {unidad.nombre}
                      </option>
                    ))}
                  </select>
                </Campo>
              </div>
            </div>

            <div className={formulario.seccion}>
              <div className={formulario.rejilla2}>
                <Campo
                  etiqueta="Precio contado (S/)"
                  ayuda="Lo que paga un cliente que cancela en el momento."
                  obligatorio
                  htmlFor="precio_contado"
                >
                  <input
                    id="precio_contado"
                    name="precio_contado"
                    type="number"
                    step="0.01"
                    min="0"
                    inputMode="decimal"
                    className="campo-entrada"
                    required
                  />
                </Campo>
                <Campo
                  etiqueta="Precio de lista (S/)"
                  ayuda="Lo que paga quien lo lleva a crédito. Suele ser igual o mayor al precio contado."
                  obligatorio
                  htmlFor="precio_lista"
                >
                  <input
                    id="precio_lista"
                    name="precio_lista"
                    type="number"
                    step="0.01"
                    min="0"
                    inputMode="decimal"
                    className="campo-entrada"
                    required
                  />
                </Campo>
              </div>

              <Campo
                etiqueta="Modalidad de venta a crédito"
                ayuda="Define si este producto se puede pagar a fin de mes, en cuotas, o de las dos formas."
              >
                <div className={formulario.opciones}>
                  <label className={formulario.opcion}>
                    <input type="checkbox" name="permite_fin_de_mes" defaultChecked /> Fin de mes
                  </label>
                  <label className={formulario.opcion}>
                    <input type="checkbox" name="permite_cuotas" /> Cuotas
                  </label>
                </div>
              </Campo>
            </div>

            <div className={formulario.acciones}>
              <Boton variante="secundario" onClick={cerrarModal}>
                Cancelar
              </Boton>
              <Boton type="submit">Guardar producto</Boton>
            </div>
          </form>
        </Modal>
      )}
    </Shell>
  )
}
