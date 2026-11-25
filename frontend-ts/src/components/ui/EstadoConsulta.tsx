import { Aviso } from './Aviso'
import { Boton } from './Boton'

export function EstadoConsulta({ cargando, error, recargar }: { cargando?: boolean; error?: string; recargar?: () => void }) {
  if (cargando) return <Aviso tono="info">Cargando…</Aviso>
  if (!error) return null
  return (
    <Aviso tono="peligro">
      <p>{error}</p>
      {recargar && <Boton variante="fantasma" tamano="pequeno" onClick={recargar}>Volver a intentar</Boton>}
    </Aviso>
  )
}
