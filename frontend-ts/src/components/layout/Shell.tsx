import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useSesion } from '../../contexts/sesion'
import { Icono } from '../ui/Icono'
import { SelectorTema } from '../ui/SelectorTema'
import { BarraLateral } from './BarraLateral'
import { NOMBRE_APLICACION, NOMBRE_ROL } from './navegacion'
import styles from './Shell.module.css'

interface ShellProps {
  titulo: string
  subtitulo?: string
  /** Línea pequeña sobre el título. Por defecto, la tienda o el rol de quien inició sesión. */
  antetitulo?: string
  /** Botones de la página, a la derecha del título. */
  acciones?: ReactNode
  children: ReactNode
}

// A partir de este ancho la barra lateral está siempre a la vista (coincide con Shell.module.css).
const CONSULTA_ESCRITORIO = '(min-width: 861px)'

/** El marco de toda pantalla con sesión: barra lateral + barra superior + contenido. */
export function Shell({ titulo, subtitulo, antetitulo, acciones, children }: ShellProps) {
  const { sesion } = useSesion()
  const [menuAbierto, setMenuAbierto] = useState(false)
  const cerrarMenu = useCallback(() => setMenuAbierto(false), [])

  // Menú del teléfono: Escape lo cierra y, mientras está abierto, la página de atrás no se desplaza.
  useEffect(() => {
    if (!menuAbierto) return
    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key === 'Escape') setMenuAbierto(false)
    }
    const desbordePrevio = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', alPresionarTecla)
    return () => {
      document.body.style.overflow = desbordePrevio
      document.removeEventListener('keydown', alPresionarTecla)
    }
  }, [menuAbierto])

  // Si la ventana crece hasta el tamaño de escritorio, el menú del teléfono deja de tener sentido.
  useEffect(() => {
    const consulta = window.matchMedia(CONSULTA_ESCRITORIO)
    function alCambiar() {
      if (consulta.matches) setMenuAbierto(false)
    }
    consulta.addEventListener('change', alCambiar)
    return () => consulta.removeEventListener('change', alCambiar)
  }, [])

  const antetituloVisible = antetitulo ?? sesion?.tiendaNombre ?? (sesion ? NOMBRE_ROL[sesion.rol] : undefined)

  return (
    <div className={styles.escenario}>
      <div className={styles.marco}>
        <div id="menu-principal" className={[styles.lateral, menuAbierto ? styles.lateralAbierto : ''].join(' ')}>
          <BarraLateral alNavegar={cerrarMenu} />
        </div>

        <button
          type="button"
          className={[styles.velo, menuAbierto ? styles.veloVisible : ''].join(' ')}
          aria-label="Cerrar menú"
          tabIndex={menuAbierto ? 0 : -1}
          onClick={cerrarMenu}
        />

        <div className={styles.panel}>
          <div className={styles.barraMovil}>
            <button
              type="button"
              className={styles.botonMenu}
              aria-label="Abrir menú"
              aria-expanded={menuAbierto}
              aria-controls="menu-principal"
              onClick={() => setMenuAbierto(true)}
            >
              <Icono nombre="menu" />
            </button>
            <span className={styles.marcaMovil}>{NOMBRE_APLICACION}</span>
            <SelectorTema />
          </div>

          <header className={styles.encabezado}>
            <div className={styles.titulos}>
              {antetituloVisible && <p className={styles.antetitulo}>{antetituloVisible}</p>}
              <h1 className={styles.titulo}>{titulo}</h1>
              {subtitulo && <p className={styles.subtitulo}>{subtitulo}</p>}
            </div>
            <div className={styles.herramientas}>
              {acciones && <div className={styles.acciones}>{acciones}</div>}
              <div className={styles.temaEscritorio}>
                <SelectorTema />
              </div>
            </div>
          </header>

          <main className={styles.contenido}>{children}</main>
        </div>
      </div>
    </div>
  )
}
