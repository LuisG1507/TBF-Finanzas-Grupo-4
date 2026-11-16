import { NavLink } from 'react-router-dom'
import { useSesion } from '../../contexts/sesion'
import { Avatar } from '../ui/Avatar'
import { Icono } from '../ui/Icono'
import { NAV_POR_ROL, NOMBRE_APLICACION, NOMBRE_ROL } from './navegacion'
import styles from './BarraLateral.module.css'

interface BarraLateralProps {
  /** Se llama al elegir una opción; en el teléfono sirve para cerrar el menú. */
  alNavegar?: () => void
}

export function BarraLateral({ alNavegar }: BarraLateralProps) {
  const { sesion, cerrarSesion } = useSesion()
  if (!sesion) return null

  return (
    <aside className={styles.barra} aria-label="Menú principal">
      <div className={styles.marca}>
        <span className={styles.marcaIcono}>
          <Icono nombre="cuaderno" tamano={21} grosor={1.9} />
        </span>
        <span className={styles.marcaTexto}>
          <span className={styles.marcaNombre}>{NOMBRE_APLICACION}</span>
          <span className={styles.marcaDetalle}>{sesion.tiendaNombre ?? 'Plataforma'}</span>
        </span>
      </div>

      <nav className={styles.nav}>
        <p className={styles.navTitulo}>Menú</p>
        {NAV_POR_ROL[sesion.rol].map((item) => (
          <NavLink
            key={item.ruta}
            to={item.ruta}
            end={item.fin}
            title={item.etiqueta}
            onClick={alNavegar}
            className={({ isActive }) => [styles.item, isActive ? styles.itemActivo : ''].join(' ')}
          >
            <Icono nombre={item.icono} className={styles.itemIcono} />
            <span className={styles.itemEtiqueta}>{item.etiqueta}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.pie}>
        <div className={styles.usuario} title={`${sesion.nombre} · ${NOMBRE_ROL[sesion.rol]}`}>
          <Avatar nombre={sesion.nombre} tono="sobreOscuro" />
          <div className={styles.usuarioTexto}>
            <p className={styles.usuarioNombre}>{sesion.nombre}</p>
            <p className={styles.usuarioRol}>{NOMBRE_ROL[sesion.rol]}</p>
          </div>
        </div>
        <button type="button" className={styles.salir} onClick={cerrarSesion} title="Cerrar sesión">
          <Icono nombre="salir" className={styles.itemIcono} />
          <span className={styles.itemEtiqueta}>Cerrar sesión</span>
        </button>
      </div>
    </aside>
  )
}
