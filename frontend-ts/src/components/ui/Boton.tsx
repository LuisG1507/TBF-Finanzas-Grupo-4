import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import { Icono, type NombreIcono } from './Icono'
import styles from './Boton.module.css'

interface Apariencia {
  variante?: 'primario' | 'secundario' | 'suave' | 'peligro' | 'fantasma'
  tamano?: 'normal' | 'pequeno'
  icono?: NombreIcono
  anchoCompleto?: boolean
}

function clasesDe({ variante = 'primario', tamano = 'normal', anchoCompleto }: Apariencia, extra?: string) {
  return [styles.boton, styles[variante], tamano === 'pequeno' && styles.pequeno, anchoCompleto && styles.completo, extra]
    .filter(Boolean)
    .join(' ')
}

type BotonProps = ButtonHTMLAttributes<HTMLButtonElement> & Apariencia

export function Boton({ variante, tamano, icono, anchoCompleto, className, children, type = 'button', ...props }: BotonProps) {
  return (
    <button type={type} className={clasesDe({ variante, tamano, anchoCompleto }, className)} {...props}>
      {icono && <Icono nombre={icono} tamano={tamano === 'pequeno' ? 15 : 17} grosor={2} />}
      {children}
    </button>
  )
}

type EnlaceBotonProps = LinkProps & Apariencia

/** Un enlace de navegación con la apariencia de un botón. */
export function EnlaceBoton({ variante, tamano, icono, anchoCompleto, className, children, ...props }: EnlaceBotonProps) {
  return (
    <Link className={clasesDe({ variante, tamano, anchoCompleto }, className)} {...props}>
      {icono && <Icono nombre={icono} tamano={tamano === 'pequeno' ? 15 : 17} grosor={2} />}
      {children}
    </Link>
  )
}
