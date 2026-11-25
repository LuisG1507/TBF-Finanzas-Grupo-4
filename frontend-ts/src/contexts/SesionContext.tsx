import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { EVENTO_SESION_EXPIRADA, guardarToken, mensajeError, obtenerToken, pedir } from '../api/cliente'
import type { RolCodigo, Tienda } from '../types/dominio'
import { SesionContext, type Sesion } from './sesion'

interface Identidad {
  username: string
  rol: RolCodigo
  tienda_id: number | null
}

async function consultarSesion(token: string, signal?: AbortSignal): Promise<Sesion> {
  const identidad = await pedir<Identidad>('/auth/yo', { token, signal })
  const tienda = identidad.tienda_id === null ? undefined : await pedir<Tienda>('/mi-tienda', { token, signal })
  return { rol: identidad.rol, nombre: identidad.username, tiendaNombre: tienda?.nombre_comercial }
}

export function SesionProvider({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [verificando, setVerificando] = useState(() => Boolean(obtenerToken()))
  const [errorSesion, setErrorSesion] = useState<string>()

  useEffect(() => {
    const control = new AbortController()
    const token = obtenerToken()
    function alExpirar() {
      setSesion(null)
      setVerificando(false)
      setErrorSesion('Tu sesión terminó. Ingresa de nuevo para continuar.')
    }
    window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
    if (token) {
      consultarSesion(token, control.signal).then((perfil) => {
        if (!control.signal.aborted && obtenerToken() === token) setSesion(perfil)
      }).catch((error: unknown) => {
        if (!control.signal.aborted && obtenerToken() === token) {
          guardarToken(null)
          setErrorSesion(mensajeError(error))
        }
      }).finally(() => {
        if (!control.signal.aborted) setVerificando(false)
      })
    }
    return () => {
      control.abort()
      window.removeEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
    }
  }, [])

  const iniciarSesion = useCallback(async (usuario: string, clave: string) => {
    setErrorSesion(undefined)
    const respuesta = await pedir<{ access_token: string }>('/auth/login', {
      method: 'POST', token: null, cuerpo: new URLSearchParams({ username: usuario, password: clave }),
    })
    const perfil = await consultarSesion(respuesta.access_token)
    guardarToken(respuesta.access_token)
    setSesion(perfil)
  }, [])

  const cerrarSesion = useCallback(() => {
    guardarToken(null)
    setSesion(null)
    setErrorSesion(undefined)
  }, [])
  const valor = useMemo(() => ({ sesion, verificando, errorSesion, iniciarSesion, cerrarSesion }),
    [sesion, verificando, errorSesion, iniciarSesion, cerrarSesion])

  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>
}
