import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { SesionContext, type Sesion } from './sesion'

const CLAVE_ALMACENAMIENTO = 'tbf-sesion-demo'

function leerSesionGuardada(): Sesion | null {
  try {
    const guardada = sessionStorage.getItem(CLAVE_ALMACENAMIENTO)
    return guardada ? (JSON.parse(guardada) as Sesion) : null
  } catch {
    return null
  }
}

export function SesionProvider({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(leerSesionGuardada)

  useEffect(() => {
    try {
      if (sesion) sessionStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify(sesion))
      else sessionStorage.removeItem(CLAVE_ALMACENAMIENTO)
    } catch {
      // almacenamiento no disponible (modo privado, etc.): la sesión sigue funcionando en memoria
    }
  }, [sesion])

  const cerrarSesion = useCallback(() => setSesion(null), [])
  const valor = useMemo(() => ({ sesion, iniciarSesion: setSesion, cerrarSesion }), [sesion, cerrarSesion])

  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>
}
