import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { NOMBRE_APLICACION } from '../../components/layout/navegacion'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Icono, type NombreIcono } from '../../components/ui/Icono'
import { Segmentado } from '../../components/ui/Segmentado'
import { SelectorTema } from '../../components/ui/SelectorTema'
import { useSesion } from '../../contexts/sesion'
import { CLIENTE_DEMO_ID, TIENDA_DEMO, clientePorId, nombreCompleto } from '../../data/mock'
import type { RolCodigo } from '../../types/dominio'
import styles from './Login.module.css'

interface Perfil {
  rol: RolCodigo
  etiqueta: string
  descripcion: string
  /** A dónde entra cada rol después de iniciar sesión. */
  ruta: string
  nombreDemo: string
  tienda?: string
}

const clienteDemo = clientePorId(CLIENTE_DEMO_ID)

const PERFILES: Perfil[] = [
  {
    rol: 'ADMIN_SIS',
    etiqueta: 'Sistema',
    descripcion: 'Administrador del sistema: da de alta y de baja a las tiendas de la plataforma.',
    ruta: '/admin-sistema/tiendas',
    nombreDemo: 'Equipo TBF',
  },
  {
    rol: 'ADMIN_NEG',
    etiqueta: 'Negocio',
    descripcion: 'Administrador del negocio: gestiona productos, clientes, compras y pagos de su tienda.',
    ruta: '/admin-negocio',
    nombreDemo: 'Rosa Quispe',
    tienda: TIENDA_DEMO,
  },
  {
    rol: 'CLIENTE',
    etiqueta: 'Cliente',
    descripcion: 'Cliente: consulta su estado de cuenta y sus próximos pagos.',
    ruta: '/cliente/mi-cuenta',
    nombreDemo: clienteDemo ? nombreCompleto(clienteDemo) : 'Cliente',
    tienda: TIENDA_DEMO,
  },
]

const VENTAJAS: { icono: NombreIcono; texto: string }[] = [
  { icono: 'personas', texto: 'Límite de crédito, día de corte y día de pago para cada cliente.' },
  { icono: 'calendario', texto: 'Compras a fin de mes o en cuotas, con su cronograma.' },
  { icono: 'documento', texto: 'Estados de cuenta con la mora identificada aparte.' },
]

export function Login() {
  const [rol, setRol] = useState<RolCodigo>('ADMIN_NEG')
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const { iniciarSesion } = useSesion()
  const navegar = useNavigate()

  const perfil = PERFILES.find((candidato) => candidato.rol === rol) ?? PERFILES[0]

  function alEnviar(evento: FormEvent) {
    evento.preventDefault()
    iniciarSesion({ rol: perfil.rol, nombre: usuario.trim() || perfil.nombreDemo, tiendaNombre: perfil.tienda })
    navegar(perfil.ruta)
  }

  return (
    <div className={styles.escenario}>
      <div className={styles.tema}>
        <SelectorTema />
      </div>

      <div className={styles.marco}>
        <section className={styles.presentacion} aria-label={NOMBRE_APLICACION}>
          <div className={styles.marca}>
            <span className={styles.marcaIcono}>
              <Icono nombre="cuaderno" tamano={22} grosor={1.9} />
            </span>
            <span className={styles.marcaNombre}>{NOMBRE_APLICACION}</span>
          </div>

          <div className={styles.mensaje}>
            <p className={styles.lema}>El fiado de tu tienda, en orden.</p>
            <p className={styles.bajada}>
              Cuentas corrientes de crédito para negocios de barrio: bodegas, panaderías, bazares y más.
            </p>
            <ul className={styles.ventajas}>
              {VENTAJAS.map((ventaja) => (
                <li key={ventaja.icono}>
                  <span className={styles.ventajaIcono}>
                    <Icono nombre={ventaja.icono} tamano={17} />
                  </span>
                  {ventaja.texto}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className={styles.acceso}>
          <h1 className={styles.titulo}>Inicia sesión</h1>
          <p className={styles.subtitulo}>Ingresa con el usuario que te dieron para tu tienda.</p>

          <form className={styles.formulario} onSubmit={alEnviar}>
            <Campo
              etiqueta="Perfil de acceso"
              ayuda="En la versión final el sistema reconoce tu perfil al validar tu usuario; aquí lo eliges para poder mostrar las tres experiencias."
            >
              <Segmentado
                etiquetaGrupo="Perfil de acceso"
                opciones={PERFILES.map((opcion) => ({ valor: opcion.rol, etiqueta: opcion.etiqueta }))}
                valor={rol}
                onCambiar={setRol}
                anchoCompleto
              />
            </Campo>

            <Campo
              etiqueta="Usuario"
              ayuda="El usuario que te asignó el administrador de tu tienda (o del sistema, si eres administrador general)."
              htmlFor="usuario"
            >
              <input
                id="usuario"
                className="campo-entrada"
                placeholder={perfil.nombreDemo}
                value={usuario}
                onChange={(evento) => setUsuario(evento.target.value)}
                autoComplete="username"
              />
            </Campo>

            <Campo etiqueta="Contraseña" ayuda="Debe tener al menos 8 caracteres." htmlFor="clave">
              <input
                id="clave"
                type="password"
                className="campo-entrada"
                placeholder="••••••••"
                value={clave}
                onChange={(evento) => setClave(evento.target.value)}
                autoComplete="current-password"
              />
            </Campo>

            <Boton type="submit" anchoCompleto className={styles.botonEntrar}>
              Ingresar
            </Boton>
          </form>

          <p className={styles.descripcionPerfil}>{perfil.descripcion}</p>
        </section>
      </div>
    </div>
  )
}
