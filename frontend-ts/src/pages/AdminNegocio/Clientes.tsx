import { useCallback, useState, type FormEvent } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Avatar } from '../../components/ui/Avatar'
import { Boton } from '../../components/ui/Boton'
import { Buscador } from '../../components/ui/Buscador'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { Modal } from '../../components/ui/Modal'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { siguienteId, useDatos } from '../../contexts/datos'
import { nombreCompleto } from '../../data/mock'
import type { Cliente, TipoTasa } from '../../types/dominio'
import { TIPO_TASA, nombreDelPlazo } from '../../utils/etiquetas'
import { formatearSoles, formatearTasa, plural } from '../../utils/formato'
import { coincide } from '../../utils/texto'
import tabla from '../../components/ui/Tabla.module.css'
import formulario from '../../styles/formulario.module.css'
import pagina from '../../styles/pagina.module.css'

/** Plazos habituales, en días comerciales (mes de 30, año de 360). */
const PLAZOS = [360, 180, 90, 60, 30, 15, 1]

/** Si una tasa nominal no menciona su capitalización, se asume mensual. */
const CAPITALIZACION_POR_DEFECTO = 30

function nombreConMayuscula(dias: number): string {
  const nombre = nombreDelPlazo(dias)
  return `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} (${plural(dias, 'día', 'días')})`
}

/** "Nominal anual · cap. mensual" o "Efectiva anual". */
function describirTasa(tipo: TipoTasa, plazoDias: number, capitalizacionDias?: number): string {
  const base = `${TIPO_TASA[tipo]} ${nombreDelPlazo(plazoDias)}`
  return tipo === 'NOMINAL' && capitalizacionDias ? `${base} · cap. ${nombreDelPlazo(capitalizacionDias)}` : base
}

export function Clientes() {
  // La lista es compartida: un cliente nuevo aparece también en Nueva compra y en Registrar pago.
  const { clientes, agregarCliente } = useDatos()
  const [modalAbierto, setModalAbierto] = useState(false)
  const [consulta, setConsulta] = useState('')
  const cerrarModal = useCallback(() => setModalAbierto(false), [])

  const activos = clientes.filter((cliente) => cliente.activo).length
  const visibles = clientes.filter((cliente) => coincide(consulta, nombreCompleto(cliente), cliente.numero_documento))

  function alCrearCliente(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    const idCliente = siguienteId(clientes.map((cliente) => cliente.id_cliente))
    const tipoComp = datos.get('tipo_tasa_comp') as TipoTasa
    const tipoMora = datos.get('tipo_tasa_mora') as TipoTasa
    const nuevo: Cliente = {
      id_cliente: idCliente,
      tipo_documento: String(datos.get('tipo_documento')),
      numero_documento: String(datos.get('numero_documento')),
      nombres: String(datos.get('nombres')),
      apellidos: String(datos.get('apellidos')),
      telefono: String(datos.get('telefono') || '') || undefined,
      email: String(datos.get('email') || '') || undefined,
      activo: true,
      condicion: {
        id_condicion: idCliente,
        cliente_id: idCliente,
        moneda_codigo: 'PEN',
        tasa_compensatoria: Number(datos.get('tasa_compensatoria')).toFixed(7),
        tipo_tasa_comp: tipoComp,
        plazo_tasa_comp_dias: Number(datos.get('plazo_tasa_comp_dias')),
        capitaliz_comp_dias: tipoComp === 'NOMINAL' ? Number(datos.get('capitaliz_comp_dias')) : undefined,
        tasa_moratoria: Number(datos.get('tasa_moratoria')).toFixed(7),
        tipo_tasa_mora: tipoMora,
        plazo_tasa_mora_dias: Number(datos.get('plazo_tasa_mora_dias')),
        capitaliz_mora_dias: tipoMora === 'NOMINAL' ? Number(datos.get('capitaliz_mora_dias')) : undefined,
        limite_credito: Number(datos.get('limite_credito')).toFixed(2),
        max_meses: Number(datos.get('max_meses')),
        dia_corte: Number(datos.get('dia_corte')),
        hora_corte: '00:00',
        dia_pago: Number(datos.get('dia_pago')),
      },
    }
    agregarCliente(nuevo)
    setModalAbierto(false)
  }

  return (
    <Shell
      titulo="Clientes"
      subtitulo="Quiénes tienen crédito en tu tienda y bajo qué condiciones."
      acciones={
        <Boton icono="mas" onClick={() => setModalAbierto(true)}>
          Nuevo cliente
        </Boton>
      }
    >
      <Tarjeta relleno="ninguno">
        <div className={pagina.barraTabla}>
          <p className={pagina.barraTablaTexto}>
            <strong>{plural(clientes.length, 'cliente', 'clientes')}</strong> · {plural(activos, 'activo', 'activos')}
          </p>
          <Buscador valor={consulta} onCambiar={setConsulta} etiqueta="Buscar por nombre o documento" />
        </div>
        <div className={tabla.envoltura}>
          <table className={[tabla.tabla, tabla.amplia].join(' ')}>
            <colgroup>
              <col style={{ width: '26%' }} />
              <col style={{ width: '19%' }} />
              <col style={{ width: '19%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '11%' }} />
              <col style={{ width: '13%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Tasa compensatoria</th>
                <th>Tasa moratoria</th>
                <th className={tabla.numerica}>Límite</th>
                <th>Corte / pago</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((cliente) => {
                const { condicion } = cliente
                const nombre = nombreCompleto(cliente)
                return (
                  <tr key={cliente.id_cliente}>
                    <td>
                      <div className={tabla.identidad}>
                        <Avatar nombre={nombre} tono={cliente.activo ? 'suave' : 'neutro'} />
                        <div className={tabla.identidadTexto}>
                          <div className={tabla.fuerte}>{nombre}</div>
                          <div className={tabla.celdaSecundaria}>
                            {cliente.tipo_documento} {cliente.numero_documento}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className={tabla.cifras}>{formatearTasa(condicion.tasa_compensatoria)}</div>
                      <div className={tabla.celdaSecundaria}>
                        {describirTasa(condicion.tipo_tasa_comp, condicion.plazo_tasa_comp_dias, condicion.capitaliz_comp_dias)}
                      </div>
                    </td>
                    <td>
                      <div className={tabla.cifras}>{formatearTasa(condicion.tasa_moratoria)}</div>
                      <div className={tabla.celdaSecundaria}>
                        {describirTasa(condicion.tipo_tasa_mora, condicion.plazo_tasa_mora_dias, condicion.capitaliz_mora_dias)}
                      </div>
                    </td>
                    <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{formatearSoles(condicion.limite_credito)}</td>
                    <td className={tabla.sinCorte}>
                      Día {condicion.dia_corte} / día {condicion.dia_pago}
                    </td>
                    <td>
                      <Insignia texto={cliente.activo ? 'Activo' : 'Dado de baja'} tono={cliente.activo ? 'exito' : 'neutro'} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {visibles.length === 0 && <p className={tabla.vacio}>Ningún cliente coincide con «{consulta}».</p>}
      </Tarjeta>

      {modalAbierto && (
        <Modal
          titulo="Nuevo cliente"
          descripcion="Sus condiciones de crédito se aplican a las compras que haga desde hoy."
          onCerrar={cerrarModal}
          ancho={700}
        >
          <form className={formulario.formulario} onSubmit={alCrearCliente}>
            <div className={formulario.seccion}>
              <p className={formulario.seccionTitulo}>Datos generales</p>
              <div className={formulario.rejilla2}>
                <Campo etiqueta="Tipo de documento" ayuda="El documento con el que se identifica el cliente." obligatorio htmlFor="tipo_documento">
                  <select id="tipo_documento" name="tipo_documento" className="campo-entrada" defaultValue="DNI">
                    <option value="DNI">DNI</option>
                    <option value="CE">Carné de extranjería</option>
                    <option value="RUC">RUC</option>
                  </select>
                </Campo>
                <Campo etiqueta="N.° de documento" ayuda="8 dígitos si es DNI; 11 si es RUC." obligatorio htmlFor="numero_documento">
                  <input id="numero_documento" name="numero_documento" className="campo-entrada" inputMode="numeric" required />
                </Campo>
                <Campo etiqueta="Nombres" ayuda="Tal como figuran en su documento." obligatorio htmlFor="nombres">
                  <input id="nombres" name="nombres" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Apellidos" ayuda="Paterno y materno." obligatorio htmlFor="apellidos">
                  <input id="apellidos" name="apellidos" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Teléfono" ayuda="Opcional. Para avisarle de sus vencimientos." htmlFor="telefono">
                  <input id="telefono" name="telefono" type="tel" className="campo-entrada" />
                </Campo>
                <Campo etiqueta="Correo" ayuda="Opcional. Ahí recibirá su estado de cuenta." htmlFor="email">
                  <input id="email" name="email" type="email" className="campo-entrada" />
                </Campo>
              </div>
            </div>

            <div className={formulario.seccion}>
              <div>
                <p className={formulario.seccionTitulo}>Tasa de interés compensatorio</p>
                <p className={formulario.seccionDescripcion}>Es la que se cobra siempre, por el hecho de otorgar el crédito.</p>
              </div>
              <CamposDeTasa sufijo="comp" nombreTasa="tasa_compensatoria" />
            </div>

            <div className={formulario.seccion}>
              <div>
                <p className={formulario.seccionTitulo}>Tasa de interés moratorio</p>
                <p className={formulario.seccionDescripcion}>
                  Se pacta aparte de la compensatoria y solo se aplica si el cliente paga después de su fecha de pago.
                </p>
              </div>
              <CamposDeTasa sufijo="mora" nombreTasa="tasa_moratoria" />
            </div>

            <div className={formulario.seccion}>
              <p className={formulario.seccionTitulo}>Condiciones del crédito</p>
              <div className={formulario.rejilla2}>
                <Campo etiqueta="Moneda" ayuda="Por ahora el sistema opera únicamente en soles." htmlFor="moneda">
                  <select id="moneda" className="campo-entrada" disabled defaultValue="PEN">
                    <option value="PEN">Soles (PEN)</option>
                  </select>
                </Campo>
                <Campo
                  etiqueta="Límite de crédito (S/)"
                  ayuda="Tope de capital pendiente que puede tener este cliente."
                  obligatorio
                  htmlFor="limite_credito"
                >
                  <input
                    id="limite_credito"
                    name="limite_credito"
                    type="number"
                    step="0.01"
                    min="0"
                    inputMode="decimal"
                    className="campo-entrada"
                    required
                  />
                </Campo>
              </div>
              <div className={formulario.rejilla3}>
                <Campo etiqueta="Máximo de cuotas" ayuda="El mayor número de meses que se le puede ofrecer." obligatorio htmlFor="max_meses">
                  <input id="max_meses" name="max_meses" type="number" min={1} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Día de corte" ayuda="Día del mes (1 a 28) en que se cierra su período de compras." obligatorio htmlFor="dia_corte">
                  <input id="dia_corte" name="dia_corte" type="number" min={1} max={28} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Día de pago" ayuda="Día del mes (1 a 28) en que se compromete a pagar." obligatorio htmlFor="dia_pago">
                  <input id="dia_pago" name="dia_pago" type="number" min={1} max={28} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
              </div>
            </div>

            <div className={formulario.acciones}>
              <Boton variante="secundario" onClick={cerrarModal}>
                Cancelar
              </Boton>
              <Boton type="submit">Guardar cliente</Boton>
            </div>
          </form>
        </Modal>
      )}
    </Shell>
  )
}

interface CamposDeTasaProps {
  /** comp = compensatoria · mora = moratoria. Forma los nombres de los campos, iguales a los del backend. */
  sufijo: 'comp' | 'mora'
  nombreTasa: 'tasa_compensatoria' | 'tasa_moratoria'
}

/** Los cuatro datos que definen una tasa pactada. La capitalización solo se pide si la tasa es nominal. */
function CamposDeTasa({ sufijo, nombreTasa }: CamposDeTasaProps) {
  const [tipo, setTipo] = useState<TipoTasa>('NOMINAL')
  const idTipo = `tipo_tasa_${sufijo}`
  const idPlazo = `plazo_tasa_${sufijo}_dias`
  const idCapitalizacion = `capitaliz_${sufijo}_dias`

  return (
    <div className={formulario.rejilla2}>
      <Campo etiqueta="Tipo de tasa" ayuda="Nominal: necesita una capitalización. Efectiva: ya la lleva incluida." obligatorio htmlFor={idTipo}>
        <select
          id={idTipo}
          name={idTipo}
          className="campo-entrada"
          value={tipo}
          onChange={(evento) => setTipo(evento.target.value as TipoTasa)}
        >
          <option value="NOMINAL">Nominal</option>
          <option value="EFECTIVA">Efectiva</option>
        </select>
      </Campo>
      <Campo etiqueta="Tasa (%)" ayuda="Hasta 4 decimales al ingresarla; el sistema calcula con 7." obligatorio htmlFor={nombreTasa}>
        <input
          id={nombreTasa}
          name={nombreTasa}
          type="number"
          step="0.0001"
          min="0"
          inputMode="decimal"
          className="campo-entrada"
          required
        />
      </Campo>
      <Campo etiqueta="Plazo de la tasa" ayuda="A qué período corresponde la tasa que escribiste." obligatorio htmlFor={idPlazo}>
        <select id={idPlazo} name={idPlazo} className="campo-entrada" defaultValue={360}>
          {PLAZOS.map((dias) => (
            <option key={dias} value={dias}>
              {nombreConMayuscula(dias)}
            </option>
          ))}
        </select>
      </Campo>
      {tipo === 'NOMINAL' && (
        <Campo
          etiqueta="Capitalización"
          ayuda="Cada cuánto se capitaliza la tasa nominal. Si no se menciona, es mensual (30 días)."
          obligatorio
          htmlFor={idCapitalizacion}
        >
          <select id={idCapitalizacion} name={idCapitalizacion} className="campo-entrada" defaultValue={CAPITALIZACION_POR_DEFECTO}>
            {PLAZOS.map((dias) => (
              <option key={dias} value={dias}>
                {nombreConMayuscula(dias)}
              </option>
            ))}
          </select>
        </Campo>
      )}
    </div>
  )
}
