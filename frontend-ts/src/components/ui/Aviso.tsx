import type { ReactNode } from 'react'
import { Icono, type NombreIcono } from './Icono'
import styles from './Aviso.module.css'

type TonoAviso = 'exito' | 'peligro' | 'alerta' | 'info'

interface AvisoProps {
  tono: TonoAviso
  titulo?: string
  children: ReactNode
}

const ICONO_POR_TONO: Record<TonoAviso, NombreIcono> = {
  exito: 'check',
  peligro: 'alerta',
  alerta: 'alerta',
  info: 'info',
}

/** Mensaje dentro de la página: confirmaciones, errores de validación y notas. */
export function Aviso({ tono, titulo, children }: AvisoProps) {
  return (
    <div className={[styles.aviso, styles[tono]].join(' ')} role={tono === 'peligro' ? 'alert' : 'status'}>
      <Icono nombre={ICONO_POR_TONO[tono]} tamano={17} grosor={2} className={styles.icono} />
      <div className={styles.contenido}>
        {titulo && <p className={styles.titulo}>{titulo}</p>}
        {children}
      </div>
    </div>
  )
}
