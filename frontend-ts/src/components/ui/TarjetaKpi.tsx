import { MiniBarras } from '../graficos/MiniBarras'
import { Icono, type NombreIcono } from './Icono'
import { Tarjeta } from './Tarjeta'
import styles from './TarjetaKpi.module.css'

export interface VariacionKpi {
  texto: string
  /** favorable / desfavorable dependen del indicador: que suba la mora es malo, que suban los clientes es bueno. */
  tono: 'favorable' | 'desfavorable' | 'neutro'
  direccion?: 'sube' | 'baja'
}

export interface SerieKpi {
  valores: number[]
  etiquetas: string[]
  descripcion: string
}

interface TarjetaKpiProps {
  etiqueta: string
  valor: string
  icono: NombreIcono
  variacion?: VariacionKpi
  detalle?: string
  /** Tendencia de los últimos períodos, dibujada como mini-barras. */
  serie?: SerieKpi
  /** La tarjeta principal de la fila: fondo verde oscuro. Usar una sola por pantalla. */
  destacada?: boolean
}

/** Tarjeta de indicador: una cifra, su variación contra un período con nombre y su tendencia. */
export function TarjetaKpi({ etiqueta, valor, icono, variacion, detalle, serie, destacada }: TarjetaKpiProps) {
  return (
    <Tarjeta tono={destacada ? 'destacada' : 'normal'} className={[styles.kpi, destacada && styles.destacada].filter(Boolean).join(' ')}>
      <div className={styles.cabecera}>
        <p className={styles.etiqueta}>{etiqueta}</p>
        <span className={styles.icono}>
          <Icono nombre={icono} tamano={18} />
        </span>
      </div>

      <p className={styles.valor}>{valor}</p>

      {variacion && (
        <span className={[styles.variacion, styles[variacion.tono]].join(' ')}>
          {variacion.direccion && <Icono nombre={variacion.direccion} tamano={13} grosor={2.4} className={styles.variacionIcono} />}
          <span className={styles.variacionTexto}>{variacion.texto}</span>
        </span>
      )}

      {(detalle || serie) && (
        <div className={styles.pie}>
          <p className={styles.detalle}>{detalle}</p>
          {serie && (
            <MiniBarras valores={serie.valores} etiquetas={serie.etiquetas} descripcion={serie.descripcion} sobreOscuro={destacada} />
          )}
        </div>
      )}
    </Tarjeta>
  )
}
