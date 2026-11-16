import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react'
import styles from './GraficoBarras.module.css'

export interface DatoBarra {
  clave: string
  /** Texto corto bajo la barra, en el eje horizontal. */
  etiquetaEje: string
  /** Texto completo para el tooltip y los lectores de pantalla. */
  etiquetaLarga: string
  valor: number
  /** Referencia contra la que se compara el valor (por ejemplo, lo programado). Se dibuja como pista de fondo. */
  meta?: number
  /** La barra que se resalta cuando no hay ninguna bajo el cursor (por ejemplo, la semana actual). */
  destacada?: boolean
}

interface GraficoBarrasProps {
  datos: DatoBarra[]
  nombreSerie: string
  nombreMeta?: string
  /** Formato de los valores en el tooltip y en la etiqueta directa. */
  formatearValor: (valor: number) => string
  /** Formato de las marcas del eje vertical. */
  formatearEje: (valor: number) => string
  /** Qué muestra el gráfico, en una frase, para los lectores de pantalla. */
  descripcion: string
  alto?: number
}

const MARGEN = { arriba: 28, derecha: 6, abajo: 30, izquierda: 52 }
const ANCHO_BARRA_MAXIMO = 24
const RADIO_BARRA = 6

/** Marcas "redondas" para el eje vertical: 0, 200, 400… en vez de 0, 163.86, 327.72… */
function marcasDelEje(maximo: number, cantidadDeseada = 4): number[] {
  if (maximo <= 0) return [0, 1]
  const pasoBruto = maximo / cantidadDeseada
  const potencia = 10 ** Math.floor(Math.log10(pasoBruto))
  const multiplo = [1, 2, 2.5, 5, 10].find((candidato) => candidato * potencia >= pasoBruto) ?? 10
  const paso = multiplo * potencia
  const marcas: number[] = []
  for (let indice = 0; (indice - 1) * paso < maximo; indice += 1) marcas.push(indice * paso)
  return marcas
}

/** Rectángulo con las esquinas de arriba redondeadas y la base recta, apoyada en el eje. */
function trazoBarra(x: number, yArriba: number, ancho: number, yBase: number): string {
  const radio = Math.max(0, Math.min(RADIO_BARRA, ancho / 2, yBase - yArriba))
  return [
    `M${x},${yBase}`,
    `V${yArriba + radio}`,
    `Q${x},${yArriba} ${x + radio},${yArriba}`,
    `H${x + ancho - radio}`,
    `Q${x + ancho},${yArriba} ${x + ancho},${yArriba + radio}`,
    `V${yBase}`,
    'Z',
  ].join(' ')
}

/*
  Gráfico de barras en SVG propio.
  - Con el ratón: el tooltip aparece al pasar sobre la columna entera, no solo sobre la barra.
  - Con el teclado: Tab entra al gráfico y las flechas recorren las barras.
  - Táctil: un toque fija el tooltip; tocar fuera lo quita.
*/
export function GraficoBarras({
  datos,
  nombreSerie,
  nombreMeta,
  formatearValor,
  formatearEje,
  descripcion,
  alto = 280,
}: GraficoBarrasProps) {
  const contenedorRef = useRef<HTMLDivElement>(null)
  const [ancho, setAncho] = useState(0)
  const [activa, setActiva] = useState<number | null>(null)

  // El SVG se dibuja en píxeles reales del contenedor, para que el texto nunca se deforme.
  useLayoutEffect(() => {
    const contenedor = contenedorRef.current
    if (!contenedor) return
    setAncho(contenedor.clientWidth)
    const observador = new ResizeObserver((entradas) => setAncho(entradas[0].contentRect.width))
    observador.observe(contenedor)
    return () => observador.disconnect()
  }, [])

  // En pantallas táctiles el tooltip queda fijo hasta tocar fuera del gráfico.
  useEffect(() => {
    if (activa === null) return
    function alTocarFuera(evento: PointerEvent) {
      if (!contenedorRef.current?.contains(evento.target as Node)) setActiva(null)
    }
    document.addEventListener('pointerdown', alTocarFuera)
    return () => document.removeEventListener('pointerdown', alTocarFuera)
  }, [activa])

  const indiceDestacado = datos.findIndex((dato) => dato.destacada)
  const indiceResaltado = activa ?? (indiceDestacado >= 0 ? indiceDestacado : null)

  const maximo = Math.max(0, ...datos.map((dato) => Math.max(dato.valor, dato.meta ?? 0)))
  const marcas = marcasDelEje(maximo)
  const topeEje = marcas[marcas.length - 1]

  const anchoPlano = Math.max(0, ancho - MARGEN.izquierda - MARGEN.derecha)
  const altoPlano = alto - MARGEN.arriba - MARGEN.abajo
  const yBase = MARGEN.arriba + altoPlano
  const anchoBanda = datos.length > 0 ? anchoPlano / datos.length : 0
  const anchoBarra = Math.min(ANCHO_BARRA_MAXIMO, anchoBanda * 0.46)
  // En pantallas angostas las etiquetas del eje se alternan para no encimarse.
  const saltoEtiquetas = anchoBanda > 0 && anchoBanda < 44 ? 2 : 1

  const y = (valor: number) => yBase - (valor / topeEje) * altoPlano
  const centro = (indice: number) => MARGEN.izquierda + anchoBanda * (indice + 0.5)

  function alPresionarTecla(evento: KeyboardEvent<HTMLDivElement>) {
    if (datos.length === 0) return
    const actual = activa ?? (indiceDestacado >= 0 ? indiceDestacado : datos.length - 1)
    let siguiente: number | null = null
    if (evento.key === 'ArrowRight') siguiente = Math.min(actual + 1, datos.length - 1)
    else if (evento.key === 'ArrowLeft') siguiente = Math.max(actual - 1, 0)
    else if (evento.key === 'Home') siguiente = 0
    else if (evento.key === 'End') siguiente = datos.length - 1
    else if (evento.key === 'Escape') {
      setActiva(null)
      return
    }
    if (siguiente === null) return
    evento.preventDefault()
    setActiva(siguiente)
  }

  const datoActivo = activa === null ? null : datos[activa]
  const textoActivo = datoActivo
    ? `${datoActivo.etiquetaLarga}: ${nombreSerie.toLowerCase()} ${formatearValor(datoActivo.valor)}` +
      (datoActivo.meta !== undefined && nombreMeta ? `, ${nombreMeta.toLowerCase()} ${formatearValor(datoActivo.meta)}` : '')
    : ''

  // El tooltip se centra sobre la barra, sin salirse por los costados del gráfico.
  const MITAD_TOOLTIP = 96
  const izquierdaTooltip =
    activa === null ? 0 : Math.min(Math.max(centro(activa), MITAD_TOOLTIP), Math.max(MITAD_TOOLTIP, ancho - MITAD_TOOLTIP))
  const arribaTooltip = datoActivo ? y(Math.max(datoActivo.valor, datoActivo.meta ?? 0)) - 10 : 0

  return (
    <div
      ref={contenedorRef}
      className={styles.grafico}
      style={{ height: alto }}
      role="group"
      aria-roledescription="gráfico de barras"
      aria-label={`${descripcion} Usa las flechas izquierda y derecha para recorrer las barras.`}
      tabIndex={0}
      onKeyDown={alPresionarTecla}
      onBlur={() => setActiva(null)}
    >
      {ancho > 0 && (
        <svg
          width={ancho}
          height={alto}
          className={styles.lienzo}
          aria-hidden="true"
          onPointerLeave={(evento) => {
            if (evento.pointerType === 'mouse') setActiva(null)
          }}
        >
          {marcas.map((marca) => (
            <g key={marca}>
              <line
                x1={MARGEN.izquierda}
                x2={ancho - MARGEN.derecha}
                y1={y(marca)}
                y2={y(marca)}
                className={marca === 0 ? styles.eje : styles.rejilla}
              />
              <text x={MARGEN.izquierda - 10} y={y(marca)} className={styles.marcaEje} textAnchor="end" dominantBaseline="middle">
                {formatearEje(marca)}
              </text>
            </g>
          ))}

          {datos.map((dato, indice) => {
            const x = centro(indice) - anchoBarra / 2
            const resaltada = indice === indiceResaltado
            return (
              <g key={dato.clave}>
                {dato.meta !== undefined && dato.meta > 0 && (
                  <path d={trazoBarra(x, y(dato.meta), anchoBarra, yBase)} className={styles.pista} />
                )}
                {dato.valor > 0 && (
                  <path
                    d={trazoBarra(x, y(dato.valor), anchoBarra, yBase)}
                    className={resaltada ? styles.barraResaltada : styles.barra}
                  />
                )}
                {indice % saltoEtiquetas === (datos.length - 1) % saltoEtiquetas && (
                  <text
                    x={centro(indice)}
                    y={alto - 9}
                    className={resaltada ? styles.etiquetaEjeResaltada : styles.etiquetaEje}
                    textAnchor="middle"
                  >
                    {dato.etiquetaEje}
                  </text>
                )}
                {/* Etiqueta directa solo en la barra destacada, y solo mientras no hay tooltip abierto */}
                {activa === null && indice === indiceDestacado && (
                  <text
                    x={centro(indice)}
                    y={y(Math.max(dato.valor, dato.meta ?? 0)) - 9}
                    className={styles.etiquetaValor}
                    textAnchor="middle"
                  >
                    {formatearValor(dato.valor)}
                  </text>
                )}
                {/* Zona sensible: la columna completa, mucho más fácil de acertar que la barra */}
                <rect
                  x={MARGEN.izquierda + anchoBanda * indice}
                  y={0}
                  width={anchoBanda}
                  height={alto}
                  fill="transparent"
                  onPointerEnter={() => setActiva(indice)}
                  onPointerDown={() => setActiva(indice)}
                />
              </g>
            )
          })}
        </svg>
      )}

      {datoActivo && (
        <div className={styles.tooltip} style={{ left: izquierdaTooltip, top: arribaTooltip }} aria-hidden="true">
          <p className={styles.tooltipTitulo}>{datoActivo.etiquetaLarga}</p>
          <p className={styles.tooltipFila}>
            <span className={[styles.clave, styles.claveBarra].join(' ')} />
            <strong>{formatearValor(datoActivo.valor)}</strong>
            <span>{nombreSerie}</span>
          </p>
          {datoActivo.meta !== undefined && nombreMeta && (
            <p className={styles.tooltipFila}>
              <span className={[styles.clave, styles.clavePista].join(' ')} />
              <strong>{formatearValor(datoActivo.meta)}</strong>
              <span>{nombreMeta}</span>
            </p>
          )}
        </div>
      )}

      <p className="solo-lectores" aria-live="polite">
        {textoActivo}
      </p>
    </div>
  )
}
