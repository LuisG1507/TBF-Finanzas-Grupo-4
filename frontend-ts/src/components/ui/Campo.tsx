import { cloneElement, isValidElement, useId, type ReactNode } from 'react'
import { Icono } from './Icono'
import styles from './Campo.module.css'

interface CampoProps {
  etiqueta: string
  /** Texto de ayuda que se muestra siempre debajo del campo (punto 6b del enunciado). */
  ayuda?: string
  error?: string
  obligatorio?: boolean
  /** id del control. Si se omite, el campo se trata como un grupo (casillas, opciones). */
  htmlFor?: string
  children: ReactNode
}

interface AtributosAccesibles {
  'aria-describedby'?: string
  'aria-invalid'?: boolean
}

export function Campo({ etiqueta, ayuda, error, obligatorio, htmlFor, children }: CampoProps) {
  const idBase = useId()
  const idEtiqueta = `${idBase}-etiqueta`
  const idNota = ayuda || error ? `${idBase}-nota` : undefined

  // Enlaza el control con su ayuda para que los lectores de pantalla la anuncien al enfocarlo.
  const control =
    htmlFor && idNota && isValidElement<AtributosAccesibles>(children)
      ? cloneElement(children, { 'aria-describedby': idNota, ...(error ? { 'aria-invalid': true } : {}) })
      : children

  const marcaObligatorio = obligatorio && (
    <span className={styles.obligatorio} aria-hidden="true">
      {' '}
      *
    </span>
  )

  const nota = error ? (
    <p id={idNota} className={styles.error} role="alert">
      <Icono nombre="alerta" tamano={14} className={styles.iconoNota} />
      {error}
    </p>
  ) : ayuda ? (
    <p id={idNota} className={styles.ayuda}>
      <Icono nombre="info" tamano={14} className={styles.iconoNota} />
      {ayuda}
    </p>
  ) : null

  if (!htmlFor) {
    return (
      <div className={styles.campo} role="group" aria-labelledby={idEtiqueta} aria-describedby={idNota}>
        <span id={idEtiqueta} className={styles.etiqueta}>
          {etiqueta}
          {marcaObligatorio}
        </span>
        {children}
        {nota}
      </div>
    )
  }

  return (
    <div className={styles.campo}>
      <label htmlFor={htmlFor} className={styles.etiqueta}>
        {etiqueta}
        {marcaObligatorio}
      </label>
      {control}
      {nota}
    </div>
  )
}
