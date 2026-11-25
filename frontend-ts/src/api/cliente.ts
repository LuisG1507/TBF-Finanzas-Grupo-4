const CLAVE_TOKEN = 'bizon-token'
const CLAVE_TOKEN_ANTERIOR = 'tbf-token'
export const EVENTO_SESION_EXPIRADA = 'bizon-sesion-expirada'

function leerToken(): string | null {
  let token: string | null = null
  try {
    token = sessionStorage.getItem(CLAVE_TOKEN)
    if (!token) {
      token = sessionStorage.getItem(CLAVE_TOKEN_ANTERIOR)
      if (token) sessionStorage.setItem(CLAVE_TOKEN, token)
    }
    sessionStorage.removeItem(CLAVE_TOKEN_ANTERIOR)
  } catch {
    // El token leído sigue disponible en memoria si la migración del almacenamiento falla.
  }
  return token
}

let tokenActual = leerToken()

export function obtenerToken() {
  return tokenActual
}

export function guardarToken(token: string | null) {
  tokenActual = token
  try {
    if (token) sessionStorage.setItem(CLAVE_TOKEN, token)
    else sessionStorage.removeItem(CLAVE_TOKEN)
    sessionStorage.removeItem(CLAVE_TOKEN_ANTERIOR)
  } catch {
    // La sesión puede continuar en memoria si el navegador impide escribir en el almacenamiento.
  }
}

function mensajeDetalle(detalle: unknown): string | undefined {
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle.map((entrada: { loc?: string[]; msg?: string }) => {
      const campo = entrada.loc?.filter((parte) => !['body', 'query', 'path'].includes(parte)).join(' · ').replaceAll('_', ' ')
      return campo ? `${campo}: ${entrada.msg}` : entrada.msg
    }).filter(Boolean).join(' · ')
  }
  if (detalle && typeof detalle === 'object' && 'mensaje' in detalle && typeof detalle.mensaje === 'string') return detalle.mensaje
}

export class ErrorApi extends Error {
  readonly estado: number
  readonly detalle: unknown

  constructor(estado: number, detalle: unknown) {
    super(mensajeDetalle(detalle) || `El servidor respondió con un error (${estado}).`)
    this.estado = estado
    this.detalle = detalle
  }
}

export function mensajeError(error: unknown) {
  return error instanceof Error ? error.message : 'No se pudo completar la operación.'
}

interface Opciones extends Omit<RequestInit, 'body'> {
  cuerpo?: object | URLSearchParams
  token?: string | null
}

export async function pedir<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const { cuerpo, token = tokenActual, ...resto } = opciones
  const headers = new Headers(resto.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (cuerpo && !(cuerpo instanceof URLSearchParams)) headers.set('Content-Type', 'application/json')

  let respuesta: Response
  try {
    respuesta = await fetch(`/api/v1${ruta}`, {
      ...resto,
      headers,
      body: cuerpo instanceof URLSearchParams ? cuerpo : cuerpo ? JSON.stringify(cuerpo) : undefined,
    })
  } catch (error) {
    if (resto.signal?.aborted) throw error
    throw new Error('No se pudo conectar con el servidor. Comprueba la conexión y vuelve a intentarlo.')
  }

  if (respuesta.status === 401 && token && token === tokenActual) {
    guardarToken(null)
    window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA))
  }
  if (respuesta.status === 204) return undefined as T
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, datos?.detail)
  if (datos === null) throw new Error('El servidor no devolvió datos válidos.')
  return datos as T
}

/** Lee todas las páginas de los listados que comparten los parámetros de FastAPI. */
export async function pedirLista<T>(ruta: string, signal?: AbortSignal): Promise<T[]> {
  const elementos: T[] = []
  const separador = ruta.includes('?') ? '&' : '?'
  const limite = 200
  for (let desplazamiento = 0; ; desplazamiento += limite) {
    const pagina = await pedir<T[]>(`${ruta}${separador}limite=${limite}&desplazamiento=${desplazamiento}`, { signal })
    elementos.push(...pagina)
    if (pagina.length < limite) return elementos
  }
}
