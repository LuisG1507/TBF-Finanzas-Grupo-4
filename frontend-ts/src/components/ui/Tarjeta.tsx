import type { HTMLAttributes, ReactNode } from 'react'
import styles from './Tarjeta.module.css'

interface TarjetaProps extends HTMLAttributes<HTMLDivElement> {
  /** normal: superficie blanca · destacada: verde oscuro · suave: verde claro */
  tono?: 'normal' | 'destacada' | 'suave'
  /** ninguno: para tarjetas que contienen una tabla de borde a borde */
  relleno?: 'normal' | 'ninguno'
}

export function Tarjeta({ tono = 'normal', relleno = 'normal', className, ...props }: TarjetaProps) {
  const clases = [styles.tarjeta, styles[tono], relleno === 'ninguno' && styles.sinRelleno, className]
    .filter(Boolean)
    .join(' ')
  return <div className={clases} {...props} />
}

interface TarjetaEncabezadoProps {
  titulo: string
  descripcion?: string
  /** Lo que va a la derecha del título: un enlace, un selector, una leyenda. */
  accion?: ReactNode
  /** Para tarjetas sin relleno: el encabezado pone su propio margen interior. */
  conRelleno?: boolean
}

export function TarjetaEncabezado({ titulo, descripcion, accion, conRelleno }: TarjetaEncabezadoProps) {
  return (
    <div className={[styles.encabezado, conRelleno && styles.encabezadoConRelleno].filter(Boolean).join(' ')}>
      <div className={styles.encabezadoTexto}>
        <h2 className={styles.titulo}>{titulo}</h2>
        {descripcion && <p className={styles.descripcion}>{descripcion}</p>}
      </div>
      {accion && <div className={styles.accion}>{accion}</div>}
    </div>
  )
}
