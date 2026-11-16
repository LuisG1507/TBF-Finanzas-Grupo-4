import styles from './Avatar.module.css'

interface AvatarProps {
  nombre: string
  tamano?: 'pequeno' | 'mediano' | 'grande'
  /** suave: verde claro (por defecto) · neutro: gris · sobreOscuro: para la barra lateral */
  tono?: 'suave' | 'neutro' | 'sobreOscuro'
}

function iniciales(nombre: string): string {
  const palabras = nombre.trim().split(/\s+/).filter(Boolean)
  if (palabras.length === 0) return '?'
  if (palabras.length === 1) return palabras[0].slice(0, 2).toUpperCase()
  return (palabras[0][0] + palabras[1][0]).toUpperCase()
}

/** Círculo con las iniciales. Es decorativo: el nombre completo siempre va escrito al lado. */
export function Avatar({ nombre, tamano = 'mediano', tono = 'suave' }: AvatarProps) {
  return (
    <span className={[styles.avatar, styles[tamano], styles[tono]].join(' ')} aria-hidden="true">
      {iniciales(nombre)}
    </span>
  )
}
