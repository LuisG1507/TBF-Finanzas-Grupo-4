import { useTema, type PreferenciaTema } from '../../contexts/tema'
import { Segmentado, type OpcionSegmentado } from './Segmentado'

const OPCIONES: OpcionSegmentado<PreferenciaTema>[] = [
  { valor: 'claro', etiqueta: 'Tema claro', icono: 'sol' },
  { valor: 'oscuro', etiqueta: 'Tema oscuro', icono: 'luna' },
  { valor: 'sistema', etiqueta: 'Igual que el dispositivo', icono: 'automatico' },
]

/** Selector de tema: claro, oscuro o el del dispositivo. La elección se recuerda en este navegador. */
export function SelectorTema() {
  const { preferencia, cambiarPreferencia } = useTema()
  return (
    <Segmentado
      etiquetaGrupo="Tema de la aplicación"
      opciones={OPCIONES}
      valor={preferencia}
      onCambiar={cambiarPreferencia}
      soloIconos
    />
  )
}
