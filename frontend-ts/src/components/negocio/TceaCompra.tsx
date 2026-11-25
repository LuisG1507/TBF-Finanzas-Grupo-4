import { formatearPorcentaje } from '../../utils/formato'
import { Campo } from '../ui/Campo'

export function TceaCompra({ tasa }: { tasa: string | null }) {
  return (
    <Campo etiqueta="TCEA" ayuda="Costo anual equivalente de esta compra, con los pagos programados; no incluye mora.">
      <strong>{tasa == null ? '—' : formatearPorcentaje(Number(tasa) / 100, 7)}</strong>
    </Campo>
  )
}
