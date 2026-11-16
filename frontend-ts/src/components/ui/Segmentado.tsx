import { useId } from 'react'
import { Icono, type NombreIcono } from './Icono'
import styles from './Segmentado.module.css'

export interface OpcionSegmentado<Valor extends string> {
  valor: Valor
  etiqueta: string
  icono?: NombreIcono
}

interface SegmentadoProps<Valor extends string> {
  /** Nombre del grupo para los lectores de pantalla. */
  etiquetaGrupo: string
  opciones: OpcionSegmentado<Valor>[]
  valor: Valor
  onCambiar: (valor: Valor) => void
  /** Muestra solo el ícono; la etiqueta queda como texto accesible y como tooltip. */
  soloIconos?: boolean
  anchoCompleto?: boolean
}

/*
  Control segmentado. Por dentro son botones de opción (radio) reales, así que el teclado
  funciona como en cualquier grupo de opciones: Tab entra al grupo y las flechas cambian la elección.
*/
export function Segmentado<Valor extends string>({
  etiquetaGrupo,
  opciones,
  valor,
  onCambiar,
  soloIconos,
  anchoCompleto,
}: SegmentadoProps<Valor>) {
  const nombre = useId()

  return (
    <div
      className={[styles.grupo, anchoCompleto && styles.completo].filter(Boolean).join(' ')}
      role="radiogroup"
      aria-label={etiquetaGrupo}
    >
      {opciones.map((opcion) => (
        <label
          key={opcion.valor}
          className={[styles.opcion, soloIconos && styles.soloIcono].filter(Boolean).join(' ')}
          title={soloIconos ? opcion.etiqueta : undefined}
        >
          <input
            type="radio"
            className={styles.entrada}
            name={nombre}
            value={opcion.valor}
            checked={opcion.valor === valor}
            onChange={() => onCambiar(opcion.valor)}
            aria-label={soloIconos ? opcion.etiqueta : undefined}
          />
          {opcion.icono && <Icono nombre={opcion.icono} tamano={16} />}
          {!soloIconos && <span>{opcion.etiqueta}</span>}
        </label>
      ))}
    </div>
  )
}
