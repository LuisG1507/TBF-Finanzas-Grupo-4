import { useCallback, useEffect, useRef, useState } from 'react'
import { mensajeError, pedir, pedirLista } from './cliente'

function useCarga<T>(ruta: string | null, cargar: (ruta: string, signal: AbortSignal) => Promise<T>) {
  const [revision, setRevision] = useState(0)
  const [respuesta, setRespuesta] = useState<{ clave: string; datos?: T; error?: string }>()
  const clave = `${ruta ?? ''}:${revision}`

  useEffect(() => {
    if (!ruta) return
    const control = new AbortController()
    cargar(ruta, control.signal).then((datos) => {
      if (!control.signal.aborted) setRespuesta({ clave, datos })
    }).catch((error: unknown) => {
      if (!control.signal.aborted) setRespuesta({ clave, error: mensajeError(error) })
    })
    return () => control.abort()
  }, [ruta, cargar, clave])

  const vigente = ruta && respuesta?.clave === clave ? respuesta : undefined
  return {
    datos: vigente?.datos,
    error: vigente?.error,
    cargando: Boolean(ruta && !vigente),
    recargar: useCallback(() => setRevision((actual) => actual + 1), []),
  }
}

const pedirConSenal = <T,>(ruta: string, signal: AbortSignal) => pedir<T>(ruta, { signal })

export function useConsulta<T>(ruta: string | null) {
  return useCarga(ruta, pedirConSenal<T>)
}

export function useLista<T>(ruta: string | null) {
  return useCarga(ruta, pedirLista<T>)
}

export function useAccion() {
  const enCurso = useRef(false)
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState<string>()

  async function ejecutar(accion: () => Promise<void>) {
    if (enCurso.current) return
    enCurso.current = true
    setOcupado(true)
    setError(undefined)
    try {
      await accion()
    } catch (fallo) {
      setError(mensajeError(fallo))
    } finally {
      enCurso.current = false
      setOcupado(false)
    }
  }

  return { ejecutar, ocupado, error, limpiarError: () => setError(undefined) }
}
