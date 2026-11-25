import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAccion } from '../../api/consultas'
import { NAV_POR_ROL, NOMBRE_APLICACION } from '../../components/layout/navegacion'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Icono, type NombreIcono } from '../../components/ui/Icono'
import { Aviso } from '../../components/ui/Aviso'
import { SelectorTema } from '../../components/ui/SelectorTema'
import { useSesion } from '../../contexts/sesion'
import styles from './Login.module.css'

const VENTAJAS: { icono: NombreIcono; texto: string }[] = [
  { icono: 'personas', texto: 'Límite de crédito, día de corte y día de pago para cada cliente.' },
  { icono: 'calendario', texto: 'Compras a fin de mes o en cuotas, con su cronograma.' },
  { icono: 'documento', texto: 'Estados de cuenta con la mora identificada aparte.' },
]

export function Login() {
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const { iniciarSesion, sesion, verificando, errorSesion } = useSesion()
  const { ejecutar, ocupado, error } = useAccion()

  function alEnviar(evento: FormEvent) {
    evento.preventDefault()
    void ejecutar(() => iniciarSesion(usuario.trim(), clave))
  }

  if (sesion) return <Navigate to={NAV_POR_ROL[sesion.rol][0].ruta} replace />

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
              etiqueta="Usuario"
              ayuda="El usuario que te asignó el administrador de tu tienda (o del sistema, si eres administrador general)."
              htmlFor="usuario"
            >
              <input
                id="usuario"
                className="campo-entrada"
                required
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
                required
              />
            </Campo>

            {(error || errorSesion) && <Aviso tono="peligro">{error ?? errorSesion}</Aviso>}
            <Boton type="submit" anchoCompleto className={styles.botonEntrar} disabled={ocupado || verificando}>
              {ocupado || verificando ? 'Validando…' : 'Ingresar'}
            </Boton>
          </form>

        </section>
      </div>
    </div>
  )
}
