import { createContext, useContext } from 'react'

/** Lo que elige la persona en el selector. "sistema" sigue el tema del dispositivo. */
export type PreferenciaTema = 'claro' | 'oscuro' | 'sistema'

/** El tema que realmente se pinta. */
export type Tema = 'claro' | 'oscuro'

export interface TemaContextValor {
  preferencia: PreferenciaTema
  tema: Tema
  cambiarPreferencia: (preferencia: PreferenciaTema) => void
}

// La misma clave se lee en index.html para aplicar el tema antes del primer pintado.
const CLAVE_ALMACENAMIENTO = 'bizon-tema'
const CLAVE_ANTERIOR = 'tbf-tema'

export const TemaContext = createContext<TemaContextValor | null>(null)

export function useTema(): TemaContextValor {
  const contexto = useContext(TemaContext)
  if (!contexto) throw new Error('useTema debe usarse dentro de TemaProvider')
  return contexto
}

export function leerPreferenciaGuardada(): PreferenciaTema {
  try {
    const actual = localStorage.getItem(CLAVE_ALMACENAMIENTO)
    const guardada = actual ?? localStorage.getItem(CLAVE_ANTERIOR)
    if (guardada === 'claro' || guardada === 'oscuro' || guardada === 'sistema') {
      if (actual === null) guardarPreferencia(guardada)
      return guardada
    }
  } catch {
    // almacenamiento no disponible (modo privado, etc.): se usa el tema del sistema
  }
  return 'sistema'
}

export function guardarPreferencia(preferencia: PreferenciaTema): void {
  try {
    localStorage.setItem(CLAVE_ALMACENAMIENTO, preferencia)
    localStorage.removeItem(CLAVE_ANTERIOR)
  } catch {
    // sin almacenamiento la preferencia igual funciona, solo que no se recuerda al recargar
  }
}
