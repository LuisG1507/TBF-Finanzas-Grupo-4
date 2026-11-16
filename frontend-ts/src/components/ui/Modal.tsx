import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Icono } from './Icono'
import styles from './Modal.module.css'

interface ModalProps {
  titulo: string
  descripcion?: string
  onCerrar: () => void
  children: ReactNode
  ancho?: number
}

export function Modal({ titulo, descripcion, onCerrar, children, ancho = 560 }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null)

  // Escape cierra el modal.
  useEffect(() => {
    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key === 'Escape') onCerrar()
    }
    document.addEventListener('keydown', alPresionarTecla)
    return () => document.removeEventListener('keydown', alPresionarTecla)
  }, [onCerrar])

  // Mientras está abierto: la página de atrás no se desplaza, el foco entra al panel
  // y al cerrar vuelve al botón que lo abrió.
  useEffect(() => {
    const focoAnterior = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const desbordePrevio = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    panelRef.current?.focus()
    return () => {
      document.body.style.overflow = desbordePrevio
      focoAnterior?.focus()
    }
  }, [])

  return createPortal(
    <div className={styles.fondo} onClick={onCerrar}>
      <div
        ref={panelRef}
        className={styles.panel}
        style={{ maxWidth: ancho }}
        onClick={(evento) => evento.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        tabIndex={-1}
      >
        <div className={styles.encabezado}>
          <div>
            <h2 className={styles.titulo}>{titulo}</h2>
            {descripcion && <p className={styles.descripcion}>{descripcion}</p>}
          </div>
          <button type="button" className={styles.cerrar} onClick={onCerrar} aria-label="Cerrar">
            <Icono nombre="cerrar" tamano={16} grosor={2} />
          </button>
        </div>
        <div className={styles.cuerpo}>{children}</div>
      </div>
    </div>,
    document.body,
  )
}
