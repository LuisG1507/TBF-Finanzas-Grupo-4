import { Icono } from './Icono'
import styles from './Buscador.module.css'

interface BuscadorProps {
  valor: string
  onCambiar: (valor: string) => void
  /** Qué se busca, por ejemplo "Buscar por nombre o RUC". Es el texto de ejemplo y el nombre accesible. */
  etiqueta: string
}

/** Campo de búsqueda para filtrar una tabla mientras se escribe. */
export function Buscador({ valor, onCambiar, etiqueta }: BuscadorProps) {
  return (
    <label className={styles.buscador}>
      <Icono nombre="buscar" tamano={16} className={styles.icono} />
      <input
        type="search"
        className={styles.entrada}
        placeholder={etiqueta}
        aria-label={etiqueta}
        value={valor}
        onChange={(evento) => onCambiar(evento.target.value)}
      />
    </label>
  )
}
