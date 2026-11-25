import type { Cuota, MonedaCodigo } from '../../types/dominio'
import { ESTADO_CUOTA } from '../../utils/etiquetas'
import { formatearFecha, formatearMonto } from '../../utils/formato'
import { Insignia } from '../ui/Insignia'
import { TceaCompra } from './TceaCompra'
import tabla from '../ui/Tabla.module.css'

export function TablaCronograma({ cuotas, moneda, tcea }: { cuotas: Cuota[]; moneda: MonedaCodigo; tcea: string | null }) {
  return (
    <>
      <div className={tabla.leyenda}><TceaCompra tasa={tcea} /></div>
      <div className={tabla.envoltura}>
        <table className={[tabla.tabla, tabla.amplia].join(' ')}>
          <thead>
            <tr>
              <th>N.°</th><th>Vencimiento</th>
              {['Saldo inicial', 'Interés', 'Amortización', 'Cuota', 'Saldo final'].map((columna) => (
                <th key={columna} className={tabla.numerica}>{columna}</th>
              ))}
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {cuotas.map((cuota) => (
              <tr key={cuota.numero}>
                <td>{cuota.numero}</td>
                <td className={tabla.sinCorte}>{formatearFecha(cuota.fecha_vencimiento)}</td>
                <td className={tabla.numerica}>{formatearMonto(cuota.saldo_inicial, moneda)}</td>
                <td className={tabla.numerica}>{formatearMonto(cuota.interes, moneda)}</td>
                <td className={tabla.numerica}>{formatearMonto(cuota.amortizacion, moneda)}</td>
                <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearMonto(cuota.monto_cuota, moneda)}</td>
                <td className={tabla.numerica}>{formatearMonto(cuota.saldo_final, moneda)}</td>
                <td><Insignia texto={ESTADO_CUOTA[cuota.estado].texto} tono={ESTADO_CUOTA[cuota.estado].tono} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
