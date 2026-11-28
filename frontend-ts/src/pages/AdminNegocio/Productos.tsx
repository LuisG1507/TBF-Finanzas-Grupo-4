import { useCallback, useState, type FormEvent } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Boton } from '../../components/ui/Boton'
import { Buscador } from '../../components/ui/Buscador'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { Modal } from '../../components/ui/Modal'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { pedir } from '../../api/cliente'
import { useAccion, useConsulta, useLista } from '../../api/consultas'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import type { Marca, Producto, Proveedor, UnidadMedida } from '../../types/dominio'
import { formatearSoles, plural } from '../../utils/formato'
import { coincide } from '../../utils/texto'
import tabla from '../../components/ui/Tabla.module.css'
import formulario from '../../styles/formulario.module.css'
import pagina from '../../styles/pagina.module.css'

export function Productos() {
  const carga = useLista<Producto>('/productos')
  const cargaMarcas = useConsulta<Marca[]>('/marcas?activo=true')
  const cargaProveedores = useConsulta<Proveedor[]>('/proveedores?activo=true')
  const cargaUnidades = useConsulta<UnidadMedida[]>('/unidades-medida')
  const productos = carga.datos ?? []
  const accion = useAccion()
  const [catalogo, setCatalogo] = useState<'marca' | 'proveedor' | null>(null)
  const cerrarCatalogo = useCallback(() => setCatalogo(null), [])
  const [modalAbierto, setModalAbierto] = useState(false)
  const [consulta, setConsulta] = useState('')
  const cerrarModal = useCallback(() => setModalAbierto(false), [])

  const activos = productos.filter((producto) => producto.activo).length
  const visibles = productos.filter((producto) =>
    coincide(consulta, producto.nombre, producto.codigo, producto.marca?.nombre),
  )

  function alCrearProducto(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    void accion.ejecutar(async () => {
      await pedir('/productos', {
        method: 'POST',
        cuerpo: {
          codigo: datos.get('codigo'),
          nombre: datos.get('nombre'),
          descripcion: datos.get('descripcion') || null,
          imagen_url: datos.get('imagen_url') || null,
          proveedor_id: datos.get('proveedor_id') ? Number(datos.get('proveedor_id')) : null,
          marca_id: datos.get('marca_id') ? Number(datos.get('marca_id')) : null,
          unidad_id: Number(datos.get('unidad_id')),
          precio_contado: datos.get('precio_contado'),
          precio_lista: datos.get('precio_lista'),
          permite_fin_de_mes: datos.has('permite_fin_de_mes'),
          permite_cuotas: datos.has('permite_cuotas'),
        },
      })
      carga.recargar()
      setModalAbierto(false)
    })
  }

  function alternarProducto(producto: Producto) {
    void accion.ejecutar(async () => {
      await pedir('/productos/' + producto.id_producto + '/' + (producto.activo ? 'baja' : 'alta'), { method: 'POST' })
      carga.recargar()
    })
  }

  function crearCatalogo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const nombre = new FormData(evento.currentTarget).get('nombre')
    const esMarca = catalogo === 'marca'
    void accion.ejecutar(async () => {
      await pedir(esMarca ? '/marcas' : '/proveedores', {
        method: 'POST', cuerpo: esMarca ? { nombre } : { razon_social: nombre },
      })
      if (esMarca) cargaMarcas.recargar()
      else cargaProveedores.recargar()
      cerrarCatalogo()
    })
  }

  return (
    <Shell
      titulo="Productos"
      subtitulo="Lo que tu tienda ofrece a crédito, con su precio al contado y su precio de lista."
      acciones={
        <>
          <Boton variante="secundario" onClick={() => { accion.limpiarError(); setCatalogo('marca') }}>Nueva marca</Boton>
          <Boton variante="secundario" onClick={() => { accion.limpiarError(); setCatalogo('proveedor') }}>Nuevo proveedor</Boton>
          <Boton icono="mas" onClick={() => { accion.limpiarError(); setModalAbierto(true) }}>Nuevo producto</Boton>
        </>
      }
    >
      <EstadoConsulta {...carga} />
      {!modalAbierto && !catalogo && <EstadoConsulta error={accion.error} />}
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
                const marca = producto.marca?.nombre
                return (
                  <tr key={producto.id_producto}>
                    <td>
                      <div className={tabla.fuerte}>{producto.nombre}</div>
                      <div className={tabla.celdaSecundaria}>
                        {producto.codigo}
                        {marca ? ` · ${marca}` : ''}
                      </div>
                    </td>
                    <td>{producto.unidad.codigo}</td>
                    <td className={tabla.numerica}>{formatearSoles(producto.precio_contado)}</td>
                    <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(producto.precio_lista)}</td>
                    <td>
                      <div className={tabla.grupoInsignias}>
                        {producto.permite_fin_de_mes && <Insignia texto="Fin de mes" />}
                        {producto.permite_cuotas && <Insignia texto="Cuotas" />}
                      </div>
                    </td>
                    <td>
                      <div className={tabla.estadoConAccion}>
                      <Insignia texto={producto.activo ? 'Activo' : 'Dado de baja'} tono={producto.activo ? 'exito' : 'neutro'} />
                      <Boton variante="fantasma" tamano="pequeno" disabled={accion.ocupado} onClick={() => alternarProducto(producto)}>
                        {producto.activo ? 'Dar de baja' : 'Reactivar'}
                      </Boton>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {carga.datos && visibles.length === 0 && <p className={tabla.vacio}>{consulta.trim() ? <>Ningún producto coincide con «{consulta}».</> : 'Todavía no hay productos. Agrégalos con «Nuevo producto».'}</p>}
      </Tarjeta>

      {catalogo && (
        <Modal titulo={catalogo === 'marca' ? 'Nueva marca' : 'Nuevo proveedor'} onCerrar={cerrarCatalogo}>
          <form className={formulario.formulario} onSubmit={crearCatalogo}>
            <EstadoConsulta error={accion.error} />
            <Campo etiqueta={catalogo === 'marca' ? 'Nombre de la marca' : 'Razón social'} obligatorio htmlFor="catalogo-nombre">
              <input id="catalogo-nombre" name="nombre" className="campo-entrada" required maxLength={catalogo === 'marca' ? 100 : 200} />
            </Campo>
            <div className={formulario.acciones}><Boton type="submit" disabled={accion.ocupado}>Guardar</Boton></div>
          </form>
        </Modal>
      )}

      {modalAbierto && (
        <Modal titulo="Nuevo producto" descripcion="Aparecerá de inmediato al registrar una compra." onCerrar={cerrarModal} ancho={660}>
          <form className={formulario.formulario} onSubmit={alCrearProducto}>
            <EstadoConsulta error={accion.error} />
            <EstadoConsulta {...cargaMarcas} />
            <EstadoConsulta {...cargaProveedores} />
            <EstadoConsulta {...cargaUnidades} />
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
              <Campo etiqueta="URL de la imagen" htmlFor="imagen_url">
                <input id="imagen_url" name="imagen_url" type="url" className="campo-entrada" />
              </Campo>

              <div className={formulario.rejilla3}>
                <Campo etiqueta="Proveedor" ayuda="Opcional, si lo compras a un proveedor fijo." htmlFor="proveedor_id">
                  <select id="proveedor_id" name="proveedor_id" className="campo-entrada" defaultValue="">
                    <option value="">Sin proveedor</option>
                    {(cargaProveedores.datos ?? []).map((proveedor) => (
                      <option key={proveedor.id_proveedor} value={proveedor.id_proveedor}>
                        {proveedor.razon_social}
                      </option>
                    ))}
                  </select>
                </Campo>
                <Campo etiqueta="Marca" ayuda="Opcional; no aplica a servicios." htmlFor="marca_id">
                  <select id="marca_id" name="marca_id" className="campo-entrada" defaultValue="">
                    <option value="">Sin marca</option>
                    {(cargaMarcas.datos ?? []).map((marca) => (
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
                    {(cargaUnidades.datos ?? []).map((unidad) => (
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
              <Boton type="submit" disabled={accion.ocupado || !cargaUnidades.datos}>{accion.ocupado ? 'Guardando…' : 'Guardar producto'}</Boton>
            </div>
          </form>
        </Modal>
      )}
    </Shell>
  )
}
