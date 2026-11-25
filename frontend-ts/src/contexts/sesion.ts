import { createContext, useContext } from 'react'
import type { RolCodigo } from '../types/dominio'

export interface Sesion {
  rol: RolCodigo
  nombre: string
  tiendaNombre?: string
}

export interface SesionContextValor {
  sesion: Sesion | null
  verificando: boolean
  errorSesion: string | undefined
  iniciarSesion: (usuario: string, clave: string) => Promise<void>
  cerrarSesion: () => void
}

export const SesionContext = createContext<SesionContextValor | null>(null)

export function useSesion(): SesionContextValor {
  const contexto = useContext(SesionContext)
  if (!contexto) throw new Error('useSesion debe usarse dentro de SesionProvider')
  return contexto
}
