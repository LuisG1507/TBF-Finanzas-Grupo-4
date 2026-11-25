import type { Compra } from '../../types/dominio'
import { formatearFecha, formatearMonto } from '../../utils/formato'
import { FilaDato, ListaDatos } from '../ui/ListaDatos'
import { TablaCronograma } from './TablaCronograma'
import { TceaCompra } from './TceaCompra'

export function DetalleCompra({ compra }: { compra: Compra }) {
  const moneda = compra.moneda.codigo_iso
  return (
    <>
      <ListaDatos>
        <FilaDato etiqueta="Fecha de corte" valor={formatearFecha(compra.fecha_corte)} />
        <FilaDato etiqueta="Primer vencimiento" valor={formatearFecha(compra.fecha_primer_pago)} />
        <FilaDato etiqueta="Días de gracia" valor={String(compra.dias_gracia)} />
        <FilaDato etiqueta="Interés total" valor={formatearMonto(compra.total_intereses, moneda)} />
        <FilaDato etiqueta="Total a pagar" valor={formatearMonto(compra.total_a_pagar, moneda)} enfasis />
      </ListaDatos>
      {compra.cronograma.length > 0
        ? <TablaCronograma cuotas={compra.cronograma} moneda={moneda} tcea={compra.tcea_pct} />
        : <TceaCompra tasa={compra.tcea_pct} />}
    </>
  )
}
