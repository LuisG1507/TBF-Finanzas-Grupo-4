import { useCallback, useState, type FormEvent } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Avatar } from '../../components/ui/Avatar'
import { Boton } from '../../components/ui/Boton'
import { Buscador } from '../../components/ui/Buscador'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { Modal } from '../../components/ui/Modal'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { pedir } from '../../api/cliente'
import { useAccion, useLista } from '../../api/consultas'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import type { Tienda } from '../../types/dominio'
import { plural } from '../../utils/formato'
import { coincide } from '../../utils/texto'
import tabla from '../../components/ui/Tabla.module.css'
import formulario from '../../styles/formulario.module.css'
import pagina from '../../styles/pagina.module.css'

const GIROS = ['Bodega', 'Panadería', 'Carnicería', 'Pollería', 'Pescadería', 'Bazar', 'Licorería', 'Peluquería', 'Spa', 'Otro']

export function Tiendas() {
  const carga = useLista<Tienda>('/tiendas')
  const tiendas = carga.datos ?? []
  const accion = useAccion()
  const [modalAbierto, setModalAbierto] = useState(false)
  const [consulta, setConsulta] = useState('')
  const cerrarModal = useCallback(() => setModalAbierto(false), [])

  const activas = tiendas.filter((tienda) => tienda.activo).length
  const visibles = tiendas.filter((tienda) =>
    coincide(consulta, tienda.nombre_comercial, tienda.razon_social, tienda.ruc, tienda.giro),
  )

  function alCrearTienda(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    void accion.ejecutar(async () => {
      await pedir('/tiendas', {
        method: 'POST',
        cuerpo: {
          ruc: datos.get('ruc'),
          razon_social: datos.get('razon_social'),
          nombre_comercial: datos.get('nombre_comercial'),
          giro: datos.get('giro'),
          direccion: datos.get('direccion') || null,
          telefono: datos.get('telefono') || null,
          email: datos.get('email') || null,
          admin_username: datos.get('usuario_admin'),
          admin_password: datos.get('clave_admin'),
        },
      })
      carga.recargar()
      setModalAbierto(false)
    })
  }

  function alternarTienda(tienda: Tienda) {
    const operacion = tienda.activo ? 'baja' : 'alta'
    void accion.ejecutar(async () => {
      await pedir('/tiendas/' + tienda.id_tienda + '/' + operacion, { method: 'POST' })
      carga.recargar()
    })
  }

  return (
    <Shell
      titulo="Tiendas"
      subtitulo="Da de alta o de baja a las tiendas que operan en la plataforma."
      acciones={
        <Boton icono="mas" onClick={() => { accion.limpiarError(); setModalAbierto(true) }}>
          Nueva tienda
        </Boton>
      }
    >
      <EstadoConsulta {...carga} />
      {!modalAbierto && <EstadoConsulta error={accion.error} />}
      <Tarjeta relleno="ninguno">
        <div className={pagina.barraTabla}>
          <p className={pagina.barraTablaTexto}>
            <strong>{plural(tiendas.length, 'tienda', 'tiendas')}</strong> · {plural(activas, 'activa', 'activas')} ·{' '}
            {plural(tiendas.length - activas, 'dada de baja', 'dadas de baja')}
          </p>
          <Buscador valor={consulta} onCambiar={setConsulta} etiqueta="Buscar por nombre, RUC o giro" />
        </div>
        <div className={tabla.envoltura}>
          <table className={tabla.tabla}>
            <colgroup>
              <col style={{ width: '31%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '15%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '14%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Tienda</th>
                <th>RUC</th>
                <th>Giro</th>
                <th>Teléfono</th>
                <th>Estado</th>
                <th>
                  <span className="solo-lectores">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((tienda) => (
                <tr key={tienda.id_tienda}>
                  <td>
                    <div className={tabla.identidad}>
                      <Avatar nombre={tienda.nombre_comercial} tono={tienda.activo ? 'suave' : 'neutro'} />
                      <div className={tabla.identidadTexto}>
                        <div className={tabla.fuerte}>{tienda.nombre_comercial}</div>
                        <div className={tabla.celdaSecundaria}>{tienda.razon_social}</div>
                      </div>
                    </div>
                  </td>
                  <td className={tabla.cifras}>{tienda.ruc}</td>
                  <td className={tabla.sinCorte}>{tienda.giro}</td>
                  <td className={tabla.sinCorte}>{tienda.telefono ?? '—'}</td>
                  <td>
                    <Insignia texto={tienda.activo ? 'Activa' : 'Dada de baja'} tono={tienda.activo ? 'exito' : 'neutro'} />
                  </td>
                  <td>
                    <div className={tabla.celdaAcciones}>
                      <Boton variante="fantasma" tamano="pequeno" disabled={accion.ocupado} onClick={() => alternarTienda(tienda)}>
                        {tienda.activo ? 'Dar de baja' : 'Reactivar'}
                      </Boton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {carga.datos && visibles.length === 0 && <p className={tabla.vacio}>Ninguna tienda coincide con «{consulta}».</p>}
      </Tarjeta>

      {modalAbierto && (
        <Modal
          titulo="Nueva tienda"
          descripcion="La tienda queda activa y su administrador puede ingresar de inmediato."
          onCerrar={cerrarModal}
          ancho={640}
        >
          <form className={formulario.formulario} onSubmit={alCrearTienda}>
            <EstadoConsulta error={accion.error} />
            <div className={formulario.seccion}>
              <div className={formulario.rejilla2}>
                <Campo etiqueta="RUC" ayuda="11 dígitos, tal como figura en SUNAT." obligatorio htmlFor="ruc">
                  <input
                    id="ruc"
                    name="ruc"
                    className="campo-entrada"
                    required
                    pattern="\d{11}"
                    maxLength={11}
                    inputMode="numeric"
                    placeholder="10458963201"
                  />
                </Campo>
                <Campo etiqueta="Giro del negocio" ayuda="El sistema funciona igual para cualquier giro." obligatorio htmlFor="giro">
                  <select id="giro" name="giro" className="campo-entrada" required defaultValue="">
                    <option value="" disabled>
                      Selecciona uno
                    </option>
                    {GIROS.map((giro) => (
                      <option key={giro} value={giro}>
                        {giro}
                      </option>
                    ))}
                  </select>
                </Campo>
              </div>

              <Campo
                etiqueta="Razón social"
                ayuda="El nombre legal de la tienda, tal como figura en su RUC."
                obligatorio
                htmlFor="razon_social"
              >
                <input id="razon_social" name="razon_social" className="campo-entrada" required placeholder="Rosa Elvira Quispe Mamani" />
              </Campo>

              <Campo
                etiqueta="Nombre comercial"
                ayuda="Como la van a reconocer sus clientes, por ejemplo «Bodega Don Rosendo»."
                obligatorio
                htmlFor="nombre_comercial"
              >
                <input id="nombre_comercial" name="nombre_comercial" className="campo-entrada" required />
              </Campo>

              <div className={formulario.rejilla2}>
                <Campo etiqueta="Teléfono" ayuda="Para que el equipo de soporte pueda contactar a la tienda." htmlFor="telefono">
                  <input id="telefono" name="telefono" type="tel" className="campo-entrada" placeholder="987 654 321" />
                </Campo>
                <Campo etiqueta="Correo" ayuda="Opcional, para notificaciones administrativas." htmlFor="email">
                  <input id="email" name="email" type="email" className="campo-entrada" />
                </Campo>
              </div>

              <Campo etiqueta="Dirección" ayuda="Opcional. Ayuda a identificar la tienda ante reclamos o visitas." htmlFor="direccion">
                <input id="direccion" name="direccion" className="campo-entrada" />
              </Campo>
            </div>

            <div className={formulario.seccion}>
              <div>
                <p className={formulario.seccionTitulo}>Credenciales del administrador del negocio</p>
                <p className={formulario.seccionDescripcion}>Con ellas el dueño de la tienda entra a administrar sus productos y clientes.</p>
              </div>
              <div className={formulario.rejilla2}>
                <Campo etiqueta="Usuario" ayuda="Sin espacios; por ejemplo, el nombre de la tienda." obligatorio htmlFor="usuario_admin">
                  <input id="usuario_admin" name="usuario_admin" className="campo-entrada" required autoComplete="off" />
                </Campo>
                <Campo
                  etiqueta="Contraseña temporal"
                  ayuda="Mínimo 8 caracteres. Se le pedirá cambiarla en su primer ingreso."
                  obligatorio
                  htmlFor="clave_admin"
                >
                  <input
                    id="clave_admin"
                    name="clave_admin"
                    type="password"
                    className="campo-entrada"
                    required
                    minLength={8}
                    autoComplete="new-password"
                  />
                </Campo>
              </div>
            </div>

            <div className={formulario.acciones}>
              <Boton variante="secundario" onClick={cerrarModal}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={accion.ocupado}>{accion.ocupado ? 'Creando…' : 'Crear tienda'}</Boton>
            </div>
          </form>
        </Modal>
      )}
    </Shell>
  )
}
