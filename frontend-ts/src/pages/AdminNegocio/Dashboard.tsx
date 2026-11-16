import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BarraSegmentada, type Segmento } from '../../components/graficos/BarraSegmentada'
import { GraficoBarras, type DatoBarra } from '../../components/graficos/GraficoBarras'
import { LeyendaGrafico } from '../../components/graficos/LeyendaGrafico'
import { MiniTendencia } from '../../components/graficos/MiniTendencia'
import { Shell } from '../../components/layout/Shell'
import { Avatar } from '../../components/ui/Avatar'
import { EnlaceBoton } from '../../components/ui/Boton'
import { Icono } from '../../components/ui/Icono'
import { Insignia } from '../../components/ui/Insignia'
import { Medidor } from '../../components/ui/Medidor'
import { Segmentado } from '../../components/ui/Segmentado'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import { TarjetaKpi } from '../../components/ui/TarjetaKpi'
import { useDatos } from '../../contexts/datos'
import { HOY_DEMO, cierresMensualesDemo, cobranzaSemanalDemo, cuotasDelMesDemo, nombreCompleto, posicionesDemo } from '../../data/mock'
import { SITUACION_CLIENTE } from '../../utils/etiquetas'
import {
  formatearFechaCorta,
  formatearFechaLarga,
  formatearPorcentaje,
  formatearRango,
  formatearSoles,
  formatearSolesEntero,
  formatearVariacion,
  nombreDelMes,
  plural,
  sumarMontos,
} from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import styles from './Dashboard.module.css'

/** Tramos de antigüedad de la deuda, por días de atraso del pago vencido más antiguo. */
const TRAMOS_ANTIGUEDAD: { clave: string; etiqueta: string; tono: Segmento['tono']; desde: number; hasta: number }[] = [
  { clave: 'al-dia', etiqueta: 'Al día', tono: 'bien', desde: 0, hasta: 0 },
  { clave: '1-30', etiqueta: '1 a 30 días', tono: 'aviso', desde: 1, hasta: 30 },
  { clave: '31-60', etiqueta: '31 a 60 días', tono: 'serio', desde: 31, hasta: 60 },
  { clave: 'mas-60', etiqueta: 'Más de 60 días', tono: 'critico', desde: 61, hasta: Infinity },
]

export function Dashboard() {
  // Los clientes salen de la lista compartida, así el conteo incluye a los recién registrados.
  const { clientes } = useDatos()
  const [vistaCobranza, setVistaCobranza] = useState<'grafico' | 'tabla'>('grafico')

  // Los meses de las tendencias: los cierres anteriores más el mes en curso.
  const meses = [...cierresMensualesDemo.map((cierre) => cierre.mes), HOY_DEMO]
  const mesActual = nombreDelMes(HOY_DEMO)
  const mesAnterior = nombreDelMes(meses[meses.length - 2])
  const etiquetasPorMes = (valores: number[], formatear: (valor: number) => string) =>
    valores.map((valor, indice) => `${nombreDelMes(meses[indice])}: ${formatear(valor)}`)

  // ---------- Saldo por cobrar ----------
  const saldoPorCobrar = sumarMontos(posicionesDemo.map((posicion) => posicion.saldo_capital))
  const saldosPorMes = meses.map((_, indice) =>
    sumarMontos(posicionesDemo.map((posicion) => [...posicion.saldos_cierre_previos, posicion.saldo_capital][indice])),
  )
  const saldoMesAnterior = saldosPorMes[saldosPorMes.length - 2]
  const variacionSaldo = (saldoPorCobrar - saldoMesAnterior) / saldoMesAnterior

  // ---------- Cuotas del mes ----------
  const totalCuotasMes = sumarMontos(cuotasDelMesDemo.map((cuota) => cuota.monto))
  const cuotasCobradas = cuotasDelMesDemo.filter((cuota) => cuota.estado === 'PAGADA')
  const cuotasPorMes = [...cierresMensualesDemo.map((cierre) => Number(cierre.cuotas_programadas)), totalCuotasMes]

  // ---------- Mora acumulada ----------
  const moraAcumulada = sumarMontos(posicionesDemo.map((posicion) => posicion.mora_acumulada))
  const clientesEnMora = posicionesDemo.filter((posicion) => posicion.dias_atraso > 0).length
  const moraPorMes = [...cierresMensualesDemo.map((cierre) => Number(cierre.mora_acumulada)), moraAcumulada]
  const aumentoMora = sumarMontos([moraAcumulada, -moraPorMes[moraPorMes.length - 2]])

  // ---------- Clientes activos ----------
  const clientesActivos = clientes.filter((cliente) => cliente.activo).length
  const activosPorMes = [...cierresMensualesDemo.map((cierre) => cierre.clientes_activos), clientesActivos]
  const nuevosActivos = clientesActivos - activosPorMes[activosPorMes.length - 2]

  // ---------- Cobranza por semana ----------
  const barrasCobranza: DatoBarra[] = cobranzaSemanalDemo.map((semana, indice) => ({
    clave: semana.desde,
    etiquetaEje: formatearFechaCorta(semana.desde),
    etiquetaLarga: formatearRango(semana.desde, semana.hasta),
    valor: Number(semana.cobrado),
    meta: Number(semana.programado),
    destacada: indice === cobranzaSemanalDemo.length - 1,
  }))
  const cobradoOchoSemanas = sumarMontos(cobranzaSemanalDemo.map((semana) => semana.cobrado))
  const programadoOchoSemanas = sumarMontos(cobranzaSemanalDemo.map((semana) => semana.programado))

  // ---------- Cobranza al día (lo que ya venció este mes) ----------
  const cuotasYaVencidas = cuotasDelMesDemo.filter((cuota) => cuota.fecha_vencimiento <= HOY_DEMO)
  const vencidoALaFecha = sumarMontos(cuotasYaVencidas.map((cuota) => cuota.monto))
  const cobradoALaFecha = sumarMontos(cuotasCobradas.map((cuota) => cuota.monto))
  const cobranzaAlDia = vencidoALaFecha > 0 ? cobradoALaFecha / vencidoALaFecha : 1

  // ---------- Clientes con saldo ----------
  const filasClientes = posicionesDemo
    .filter((posicion) => Number(posicion.saldo_capital) > 0)
    .sort((a, b) => Number(b.saldo_capital) - Number(a.saldo_capital))

  // ---------- Cartera por antigüedad ----------
  const segmentosCartera: Segmento[] = TRAMOS_ANTIGUEDAD.map((tramo) => {
    const posiciones = posicionesDemo.filter(
      (posicion) =>
        Number(posicion.saldo_capital) > 0 && posicion.dias_atraso >= tramo.desde && posicion.dias_atraso <= tramo.hasta,
    )
    const monto = sumarMontos(posiciones.map((posicion) => posicion.saldo_capital))
    return {
      clave: tramo.clave,
      etiqueta: tramo.etiqueta,
      detalle: plural(posiciones.length, 'cliente', 'clientes'),
      valor: monto,
      textoValor: formatearSoles(monto),
      tono: tramo.tono,
    }
  })
  const saldoEnAtraso = sumarMontos(segmentosCartera.slice(1).map((segmento) => segmento.valor))

  return (
    <Shell
      titulo="Resumen"
      subtitulo={`Así va el fiado de tu tienda al ${formatearFechaLarga(HOY_DEMO)}.`}
      acciones={
        <>
          <EnlaceBoton to="/admin-negocio/pagos/nuevo" variante="secundario" icono="billete">
            Registrar pago
          </EnlaceBoton>
          <EnlaceBoton to="/admin-negocio/compras/nueva" icono="mas">
            Nueva compra
          </EnlaceBoton>
        </>
      }
    >
      <section className={styles.indicadores} aria-label="Indicadores del mes">
        <TarjetaKpi
          destacada
          etiqueta="Saldo por cobrar"
          valor={formatearSoles(saldoPorCobrar)}
          icono="billete"
          variacion={{
            texto: `${formatearVariacion(variacionSaldo)} vs. ${mesAnterior}`,
            tono: 'neutro',
            direccion: variacionSaldo >= 0 ? 'sube' : 'baja',
          }}
          detalle="Capital pendiente"
          serie={{
            valores: saldosPorMes,
            etiquetas: etiquetasPorMes(saldosPorMes, formatearSoles),
            descripcion: `Saldo por cobrar al cierre de cada mes, de ${nombreDelMes(meses[0])} a ${mesActual}: de ${formatearSoles(saldosPorMes[0])} a ${formatearSoles(saldoPorCobrar)}.`,
          }}
        />
        <TarjetaKpi
          etiqueta={`Cuotas de ${mesActual}`}
          valor={formatearSoles(totalCuotasMes)}
          icono="calendario"
          variacion={{ texto: `${cuotasCobradas.length} de ${cuotasDelMesDemo.length} cobradas`, tono: 'favorable' }}
          detalle="Vencen este mes"
          serie={{
            valores: cuotasPorMes,
            etiquetas: etiquetasPorMes(cuotasPorMes, formatearSoles),
            descripcion: `Cuotas programadas por mes, de ${nombreDelMes(meses[0])} a ${mesActual}: de ${formatearSoles(cuotasPorMes[0])} a ${formatearSoles(totalCuotasMes)}.`,
          }}
        />
        <TarjetaKpi
          etiqueta="Mora acumulada"
          valor={formatearSoles(moraAcumulada)}
          icono="reloj"
          variacion={
            aumentoMora > 0
              ? { texto: `+${formatearSoles(aumentoMora)} vs. ${mesAnterior}`, tono: 'desfavorable', direccion: 'sube' }
              : { texto: `Sin aumento vs. ${mesAnterior}`, tono: 'favorable' }
          }
          detalle={`${plural(clientesEnMora, 'cliente', 'clientes')} con atraso`}
          serie={{
            valores: moraPorMes,
            etiquetas: etiquetasPorMes(moraPorMes, formatearSoles),
            descripcion: `Mora acumulada al cierre de cada mes, de ${nombreDelMes(meses[0])} a ${mesActual}: de ${formatearSoles(moraPorMes[0])} a ${formatearSoles(moraAcumulada)}.`,
          }}
        />
        <TarjetaKpi
          etiqueta="Clientes activos"
          valor={String(clientesActivos)}
          icono="personas"
          variacion={
            nuevosActivos > 0
              ? { texto: `+${nuevosActivos} vs. ${mesAnterior}`, tono: 'favorable', direccion: 'sube' }
              : { texto: `Igual que en ${mesAnterior}`, tono: 'neutro' }
          }
          detalle={`de ${clientes.length} registrados`}
          serie={{
            valores: activosPorMes,
            etiquetas: etiquetasPorMes(activosPorMes, String),
            descripcion: `Clientes activos por mes, de ${nombreDelMes(meses[0])} a ${mesActual}: de ${activosPorMes[0]} a ${clientesActivos}.`,
          }}
        />
      </section>

      <div className={styles.rejilla}>
        <Tarjeta className={styles.ancha}>
          <TarjetaEncabezado
            titulo="Cobranza por semana"
            descripcion={`Últimas 8 semanas: cobraste ${formatearSoles(cobradoOchoSemanas)} de ${formatearSoles(programadoOchoSemanas)} programados.`}
            accion={
              <Segmentado
                etiquetaGrupo="Cómo ver la cobranza"
                opciones={[
                  { valor: 'grafico', etiqueta: 'Gráfico', icono: 'barras' },
                  { valor: 'tabla', etiqueta: 'Tabla', icono: 'tabla' },
                ]}
                valor={vistaCobranza}
                onCambiar={setVistaCobranza}
              />
            }
          />

          {vistaCobranza === 'grafico' ? (
            <>
              <LeyendaGrafico
                elementos={[
                  { etiqueta: 'Cobrado', muestra: 'barra' },
                  { etiqueta: 'Programado', muestra: 'pista' },
                ]}
              />
              <GraficoBarras
                datos={barrasCobranza}
                nombreSerie="Cobrado"
                nombreMeta="Programado"
                formatearValor={formatearSoles}
                formatearEje={formatearSolesEntero}
                descripcion="Cobranza de las últimas ocho semanas: lo cobrado frente a lo programado."
              />
            </>
          ) : (
            <div className={[tabla.envoltura, styles.tablaCobranza].join(' ')}>
              <table className={[tabla.tabla, tabla.angosta].join(' ')}>
                <thead>
                  <tr>
                    <th>Semana</th>
                    <th className={tabla.numerica}>Programado</th>
                    <th className={tabla.numerica}>Cobrado</th>
                    <th className={tabla.numerica}>Cumplimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {cobranzaSemanalDemo.map((semana) => (
                    <tr key={semana.desde}>
                      <td>{formatearRango(semana.desde, semana.hasta)}</td>
                      <td className={tabla.numerica}>{formatearSoles(semana.programado)}</td>
                      <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(semana.cobrado)}</td>
                      <td className={tabla.numerica}>
                        {Number(semana.programado) > 0 ? formatearPorcentaje(Number(semana.cobrado) / Number(semana.programado)) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Tarjeta>

        <Tarjeta tono="suave" className={styles.cifra}>
          <div className={styles.cifraCabecera}>
            <p className={styles.cifraEtiqueta}>Cobranza al día</p>
            <span className={styles.cifraIcono}>
              <Icono nombre="check" tamano={18} grosor={2.2} />
            </span>
          </div>
          <p className={styles.cifraValor}>{formatearPorcentaje(cobranzaAlDia)}</p>
          <p className={styles.cifraTexto}>
            de lo que ya venció en {mesActual} está cobrado: {formatearSoles(cobradoALaFecha)} de {formatearSoles(vencidoALaFecha)}.
          </p>
          <div className={styles.cifraPie}>
            <Medidor
              etiqueta={`Cobranza al día en ${mesActual}`}
              valor={cobradoALaFecha}
              maximo={vencidoALaFecha}
              textoValor={`${formatearSoles(cobradoALaFecha)} de ${formatearSoles(vencidoALaFecha)}`}
              sobreSuave
            />
            <p className={styles.cifraNota}>
              Faltan {plural(cuotasYaVencidas.length - cuotasCobradas.length, 'cuota vencida', 'cuotas vencidas')} por cobrar.
            </p>
          </div>
        </Tarjeta>

        <Tarjeta relleno="ninguno" className={styles.ancha}>
          <TarjetaEncabezado
            conRelleno
            titulo="Clientes con saldo"
            descripcion="Ordenados por lo que deben. La tendencia muestra su saldo de los últimos 6 meses."
            accion={
              <Link to="/admin-negocio/clientes" className={styles.enlace}>
                Ver todos
                <Icono nombre="chevronDerecha" tamano={14} grosor={2.2} />
              </Link>
            }
          />
          <div className={tabla.envoltura}>
            {/* La columna del cliente se queda con el espacio que sobra; las demás tienen ancho fijo */}
            <table className={tabla.tabla} style={{ minWidth: 600 }}>
              <colgroup>
                <col />
                <col style={{ width: 116 }} />
                <col style={{ width: 150 }} />
                <col style={{ width: 132 }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th className={tabla.numerica}>Saldo</th>
                  <th>Estado</th>
                  <th>Tendencia</th>
                </tr>
              </thead>
              <tbody>
                {filasClientes.map((posicion) => {
                  const cliente = clientes.find((candidato) => candidato.id_cliente === posicion.cliente_id)
                  if (!cliente) return null
                  const nombre = nombreCompleto(cliente)
                  const situacion = SITUACION_CLIENTE[posicion.situacion]
                  const saldos = [...posicion.saldos_cierre_previos, posicion.saldo_capital].map(Number)
                  return (
                    <tr key={posicion.cliente_id}>
                      <td>
                        <div className={tabla.identidad}>
                          <Avatar nombre={nombre} />
                          <div className={tabla.identidadTexto}>
                            <div className={tabla.fuerte}>{nombre}</div>
                            <div className={tabla.celdaSecundaria}>
                              {cliente.tipo_documento} {cliente.numero_documento}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(posicion.saldo_capital)}</td>
                      <td>
                        <Insignia texto={situacion.texto} tono={situacion.tono} />
                        {posicion.proximo_vencimiento && (
                          <div className={[tabla.celdaSecundaria, tabla.sinCorte, styles.vencimiento].join(' ')}>
                            {posicion.dias_atraso > 0
                              ? `Venció hace ${plural(posicion.dias_atraso, 'día', 'días')}`
                              : `Vence el ${formatearFechaCorta(posicion.proximo_vencimiento)}`}
                          </div>
                        )}
                      </td>
                      <td>
                        <MiniTendencia
                          valores={saldos}
                          descripcion={`Saldo de ${nombre} de ${nombreDelMes(meses[0])} a ${mesActual}: de ${formatearSoles(saldos[0])} a ${formatearSoles(posicion.saldo_capital)}.`}
                        />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Cartera por antigüedad"
            descripcion={
              saldoEnAtraso > 0
                ? `${formatearSoles(saldoEnAtraso)} de tu saldo por cobrar tiene algún atraso.`
                : 'Todo tu saldo por cobrar está al día.'
            }
          />
          <BarraSegmentada
            segmentos={segmentosCartera}
            descripcion="Saldo por cobrar según los días de atraso."
            formatearPorcentaje={formatearPorcentaje}
          />
        </Tarjeta>
      </div>
    </Shell>
  )
}
