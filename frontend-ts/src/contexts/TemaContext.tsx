import { useCallback, useLayoutEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { TemaContext, guardarPreferencia, leerPreferenciaGuardada, type PreferenciaTema, type Tema } from './tema'

const CONSULTA_SISTEMA_OSCURO = '(prefers-color-scheme: dark)'
const CONSULTA_SIN_ANIMACION = '(prefers-reduced-motion: reduce)'

// Color de la barra del navegador en el móvil: el mismo --color-fondo de cada tema.
const COLOR_NAVEGADOR: Record<Tema, string> = { claro: '#edf4f0', oscuro: '#060a08' }

function suscribirAlSistema(alCambiar: () => void) {
  const consulta = window.matchMedia(CONSULTA_SISTEMA_OSCURO)
  consulta.addEventListener('change', alCambiar)
  return () => consulta.removeEventListener('change', alCambiar)
}

function sistemaEnOscuro() {
  return window.matchMedia(CONSULTA_SISTEMA_OSCURO).matches
}

export function TemaProvider({ children }: { children: ReactNode }) {
  const [preferencia, setPreferencia] = useState<PreferenciaTema>(leerPreferenciaGuardada)
  const sistemaOscuro = useSyncExternalStore(suscribirAlSistema, sistemaEnOscuro)

  const tema: Tema = preferencia === 'sistema' ? (sistemaOscuro ? 'oscuro' : 'claro') : preferencia

  // useLayoutEffect: el atributo cambia en el mismo cuadro en que React pinta, sin parpadeo.
  useLayoutEffect(() => {
    document.documentElement.dataset.tema = tema
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLOR_NAVEGADOR[tema])
  }, [tema])

  const cambiarPreferencia = useCallback((nueva: PreferenciaTema) => {
    guardarPreferencia(nueva)
    const aplicar = () => flushSync(() => setPreferencia(nueva))
    const sinAnimacion = window.matchMedia(CONSULTA_SIN_ANIMACION).matches
    // Si el navegador lo permite, el cambio de tema se funde en vez de saltar.
    if (sinAnimacion || typeof document.startViewTransition !== 'function') aplicar()
    else document.startViewTransition(aplicar)
  }, [])

  const valor = useMemo(() => ({ preferencia, tema, cambiarPreferencia }), [preferencia, tema, cambiarPreferencia])

  return <TemaContext.Provider value={valor}>{children}</TemaContext.Provider>
}
