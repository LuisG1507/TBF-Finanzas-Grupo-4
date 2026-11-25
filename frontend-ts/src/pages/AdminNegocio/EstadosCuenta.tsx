import { useCallback, useState, type FormEvent } from 'react'
import { pedir } from '../../api/cliente'
import { useAccion, useLista } from '../../api/consultas'
import { Shell } from '../../components/layout/Shell'
import { TarjetasEstadosCuenta } from '../../components/negocio/TarjetasEstadosCuenta'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import { Modal } from '../../components/ui/Modal'
import { Segmentado, type OpcionSegmentado } from '../../components/ui/Segmentado'
import { Tarjeta } from '../../components/ui/Tarjeta'
import type { EstadoCuenta, EstadoCuentaEstado } from '../../types/dominio'
import { hoyLima, plural } from '../../utils/formato'
import tabla from '../../components/ui/Tabla.module.css'
import formulario from '../../styles/formulario.module.css'

type Filtro = 'TODOS' | EstadoCuentaEstado

const FILTROS: OpcionSegmentado<Filtro>[] = [
  { valor: 'TODOS', etiqueta: 'Todos' },
  { valor: 'EMITIDO', etiqueta: 'Emitidos' },
  { valor: 'VENCIDO', etiqueta: 'Vencidos' },
  { valor: 'PAGADO', etiqueta: 'Pagados' },
]

const SIN_RESULTADOS: Record<Filtro, string> = {
  TODOS: 'Todavía no se ha emitido ningún estado de cuenta.',
  EMITIDO: 'No hay estados de cuenta emitidos pendientes de pago.',
  VENCIDO: 'No hay estados de cuenta vencidos.',
  PAGADO: 'No hay estados de cuenta pagados.',
}

export function EstadosCuenta() {
  const [filtro, setFiltro] = useState<Filtro>('TODOS')
  const [generando, setGenerando] = useState(false)
  const [mensaje, setMensaje] = useState<string>()
  const cerrar = useCallback(() => setGenerando(false), [])
  const accion = useAccion()
  const carga = useLista<EstadoCuenta>('/estados-cuenta' + (filtro === 'TODOS' ? '' : '?estado=' + filtro))

  function generar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const periodo = String(new FormData(evento.currentTarget).get('periodo'))
    const [anio, mes] = periodo.split('-').map(Number)
    void accion.ejecutar(async () => {
      const emitidos = await pedir<EstadoCuenta[]>('/estados-cuenta/generar', { method: 'POST', cuerpo: { anio, mes } })
      setMensaje(emitidos.length ? plural(emitidos.length, 'estado de cuenta emitido para el mes', 'estados de cuenta emitidos para el mes') : 'El mes aún no tiene cortes listos para emitir.')
      carga.recargar()
      cerrar()
    })
  }

  return (
    <Shell
      titulo="Estados de cuenta"
      subtitulo="El listado que se genera en cada fecha de corte, con la mora identificada aparte."
      acciones={
        <>
          <Campo etiqueta="Filtrar por estado" ayuda="Vencidos muestra los estados que ya pasaron su fecha de pago y siguen pendientes.">
            <Segmentado etiquetaGrupo="Estado de cuenta" opciones={FILTROS} valor={filtro} onCambiar={setFiltro} />
          </Campo>
          <Boton icono="mas" onClick={() => { accion.limpiarError(); setGenerando(true) }}>Generar estados</Boton>
        </>
      }
    >
      {mensaje && <Aviso tono="info">{mensaje}</Aviso>}
      <EstadoConsulta {...carga} />
      {carga.datos?.length === 0 && <Tarjeta><p className={tabla.vacio}>{SIN_RESULTADOS[filtro]}</p></Tarjeta>}
      {carga.datos && <TarjetasEstadosCuenta estados={carga.datos} ruta="/estados-cuenta" />}
      {generando && (
        <Modal titulo="Generar estados de cuenta" descripcion="Se emiten los cortes del mes que ya se cumplieron." onCerrar={cerrar}>
          <form className={formulario.formulario} onSubmit={generar}>
            <EstadoConsulta error={accion.error} />
            <Campo etiqueta="Mes de corte" ayuda="Elige el mes del cierre de compras, aunque la fecha de pago caiga al mes siguiente." obligatorio htmlFor="periodo-corte">
              <input id="periodo-corte" name="periodo" type="month" className="campo-entrada"
                max={hoyLima().slice(0, 7)} defaultValue={hoyLima().slice(0, 7)} required />
            </Campo>
            <div className={formulario.acciones}><Boton type="submit" disabled={accion.ocupado}>
              {accion.ocupado ? 'Generando…' : 'Generar'}
            </Boton></div>
          </form>
        </Modal>
      )}
    </Shell>
  )
}
