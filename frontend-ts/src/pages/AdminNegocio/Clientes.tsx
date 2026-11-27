import { useCallback, useState, type FormEvent } from 'react'
import { Shell } from '../../components/layout/Shell'
import { Avatar } from '../../components/ui/Avatar'
import { Boton } from '../../components/ui/Boton'
import { Buscador } from '../../components/ui/Buscador'
import { Campo } from '../../components/ui/Campo'
import { Insignia } from '../../components/ui/Insignia'
import { Modal } from '../../components/ui/Modal'
import { Tarjeta } from '../../components/ui/Tarjeta'
import { pedir } from '../../api/cliente'
import { useAccion, useConsulta, useLista } from '../../api/consultas'
import { EstadoConsulta } from '../../components/ui/EstadoConsulta'
import type { Cliente, CondicionCredito, Moneda, TasaPactada, TipoTasa } from '../../types/dominio'
import { TIPO_TASA, nombreDelPlazo } from '../../utils/etiquetas'
import { formatearFecha, formatearMonto, formatearTasa, hoyLima, plural } from '../../utils/formato'
import { coincide, nombreCompleto } from '../../utils/texto'
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
function describirTasa(tasa: TasaPactada): string {
  const base = TIPO_TASA[tasa.tipo] + ' ' + nombreDelPlazo(tasa.plazo_dias)
  return tasa.capitalizacion_dias ? base + ' · cap. ' + nombreDelPlazo(tasa.capitalizacion_dias) : base
}

function leerTasa(datos: FormData, sufijo: 'comp' | 'mora', nombre: string) {
  const tipo = datos.get('tipo_tasa_' + sufijo)
  return {
    tipo,
    tasa_pct: datos.get(nombre),
    plazo_tasa: Number(datos.get('plazo_tasa_' + sufijo + '_dias')),
    capitalizacion: tipo === 'NOMINAL' ? Number(datos.get('capitaliz_' + sufijo + '_dias')) : null,
  }
}

export function Clientes() {
  const carga = useLista<Cliente>('/clientes')
  const clientes = carga.datos ?? []
  const accion = useAccion()
  const monedas = useConsulta<Moneda[]>('/monedas')
  const [clienteCondicion, setClienteCondicion] = useState<Cliente | null>(null)
  const [clienteHistorial, setClienteHistorial] = useState<Cliente | null>(null)
  const historial = useConsulta<CondicionCredito[]>(clienteHistorial ? '/clientes/' + clienteHistorial.id_cliente + '/condiciones' : null)
  const cerrarHistorial = useCallback(() => setClienteHistorial(null), [])
  const [modalAbierto, setModalAbierto] = useState(false)
  const [consulta, setConsulta] = useState('')
  const cerrarModal = useCallback(() => { setModalAbierto(false); setClienteCondicion(null) }, [])

  const activos = clientes.filter((cliente) => cliente.activo).length
  const visibles = clientes.filter((cliente) => coincide(consulta, nombreCompleto(cliente), cliente.numero_documento))

  function alCrearCliente(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    const condicion = {
      moneda: datos.get('moneda'),
      tasa_compensatoria: leerTasa(datos, 'comp', 'tasa_compensatoria'),
      tasa_moratoria: leerTasa(datos, 'mora', 'tasa_moratoria'),
      limite_credito: datos.get('limite_credito'),
      max_meses: Number(datos.get('max_meses')),
      dia_corte: Number(datos.get('dia_corte')),
      hora_corte: datos.get('hora_corte') || '00:00',
      dia_pago: Number(datos.get('dia_pago')),
    }
    void accion.ejecutar(async () => {
      if (clienteCondicion) {
        await pedir('/clientes/' + clienteCondicion.id_cliente + '/condicion', { method: 'PUT', cuerpo: condicion })
      } else {
        await pedir('/clientes', {
          method: 'POST',
          cuerpo: {
            tipo_documento: datos.get('tipo_documento'),
            numero_documento: datos.get('numero_documento'),
            nombres: datos.get('nombres'),
            apellidos: datos.get('apellidos'),
            telefono: datos.get('telefono') || null,
            direccion: datos.get('direccion') || null,
            email: datos.get('email') || null,
            usuario: datos.get('usuario') || null,
            password: datos.get('password'),
            condicion,
          },
        })
      }
      carga.recargar()
      cerrarModal()
    })
  }

  function alternarCliente(cliente: Cliente) {
    void accion.ejecutar(async () => {
      await pedir('/clientes/' + cliente.id_cliente + '/' + (cliente.activo ? 'baja' : 'alta'), { method: 'POST' })
      carga.recargar()
    })
  }

  const actual = clienteCondicion?.condicion

  return (
    <Shell
      titulo="Clientes"
      subtitulo="Quiénes tienen crédito en tu tienda y bajo qué condiciones."
      acciones={
        <Boton icono="mas" onClick={() => { accion.limpiarError(); setModalAbierto(true) }}>
          Nuevo cliente
        </Boton>
      }
    >
      <EstadoConsulta {...carga} />
      {!modalAbierto && <EstadoConsulta error={accion.error} />}
      <Tarjeta relleno="ninguno">
        <div className={pagina.barraTabla}>
          <p className={pagina.barraTablaTexto}>
            <strong>{plural(clientes.length, 'cliente', 'clientes')}</strong> · {plural(activos, 'activo', 'activos')}
          </p>
          <Buscador valor={consulta} onCambiar={setConsulta} etiqueta="Buscar por nombre o documento" />
        </div>
        <div className={tabla.envoltura}>
          <table className={[tabla.tabla, tabla.amplia, tabla.muyAmplia].join(' ')}>
            <colgroup>
              <col style={{ width: '19%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '15%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '24%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Tasa compensatoria</th>
                <th>Tasa moratoria</th>
                <th className={tabla.numerica}>Límite</th>
                <th>Corte / pago</th>
                <th>Estado</th>
                <th className={tabla.columnaAcciones}>Acciones</th>
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
                      <div className={tabla.cifras}>{condicion ? formatearTasa(condicion.tasa_compensatoria.tasa_pct) : '—'}</div>
                      <div className={tabla.celdaSecundaria}>
                        {condicion && describirTasa(condicion.tasa_compensatoria)}
                      </div>
                    </td>
                    <td>
                      <div className={tabla.cifras}>{condicion ? formatearTasa(condicion.tasa_moratoria.tasa_pct) : '—'}</div>
                      <div className={tabla.celdaSecundaria}>
                        {condicion && describirTasa(condicion.tasa_moratoria)}
                      </div>
                    </td>
                    <td className={[tabla.numerica, tabla.fuerte].join(' ')}>{condicion ? formatearMonto(condicion.limite_credito, condicion.moneda.codigo_iso) : '—'}</td>
                    <td className={tabla.sinCorte}>
                      {condicion ? 'Día ' + condicion.dia_corte + ' / día ' + condicion.dia_pago : '—'}
                    </td>
                    <td>
                      <Insignia texto={cliente.activo ? 'Activo' : 'Dado de baja'} tono={cliente.activo ? 'exito' : 'neutro'} />
                    </td>
                    <td>
                      <div className={tabla.celdaAcciones}>
                        <Boton variante="fantasma" tamano="pequeno" onClick={() => setClienteHistorial(cliente)}>Historial</Boton>
                        {cliente.activo && (
                          <Boton variante="fantasma" tamano="pequeno" onClick={() => { accion.limpiarError(); setClienteCondicion(cliente); setModalAbierto(true) }}>
                            Cambiar condiciones
                          </Boton>
                        )}
                        <Boton variante="fantasma" tamano="pequeno" disabled={accion.ocupado} onClick={() => alternarCliente(cliente)}>
                          {cliente.activo ? 'Dar de baja' : 'Reactivar'}
                        </Boton>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {carga.datos && visibles.length === 0 && <p className={tabla.vacio}>{consulta.trim() ? <>Ningún cliente coincide con «{consulta}».</> : 'Todavía no hay clientes. Regístralos con «Nuevo cliente».'}</p>}
      </Tarjeta>

      {clienteHistorial && (
        <Modal titulo="Historial de condiciones" descripcion={nombreCompleto(clienteHistorial)} onCerrar={cerrarHistorial} ancho={700}>
          <EstadoConsulta {...historial} />
          {historial.datos?.length === 0 && <p className={tabla.vacio}>Todavía no tiene condiciones registradas.</p>}
          {historial.datos?.map((condicion) => (
            <div key={condicion.id_condicion} className={formulario.seccion}>
              <strong>{formatearFecha(condicion.vigente_desde)} · {condicion.vigente_hasta ? 'hasta ' + formatearFecha(condicion.vigente_hasta) : 'Vigente'}</strong>
              <p>Compensatoria {formatearTasa(condicion.tasa_compensatoria.tasa_pct)} · {describirTasa(condicion.tasa_compensatoria)}</p>
              <p>Moratoria {formatearTasa(condicion.tasa_moratoria.tasa_pct)} · {describirTasa(condicion.tasa_moratoria)}</p>
              <p>{formatearMonto(condicion.limite_credito, condicion.moneda.codigo_iso)} de límite · corte {condicion.dia_corte} a las {condicion.hora_corte.slice(0, 5)} · pago {condicion.dia_pago}</p>
            </div>
          ))}
        </Modal>
      )}

      {modalAbierto && (
        <Modal
          titulo={clienteCondicion ? 'Cambiar condiciones' : 'Nuevo cliente'}
          descripcion="Sus condiciones de crédito se aplican a las compras que haga desde hoy."
          onCerrar={cerrarModal}
          ancho={700}
        >
          <form className={formulario.formulario} onSubmit={alCrearCliente}>
            <EstadoConsulta error={accion.error} />
            <EstadoConsulta {...monedas} />
            {!clienteCondicion && <div className={formulario.seccion}>
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
                <Campo etiqueta="Correo" ayuda="Opcional. Correo de contacto." htmlFor="email">
                  <input id="email" name="email" type="email" className="campo-entrada" />
                </Campo>
                <Campo etiqueta="Dirección" htmlFor="direccion"><input id="direccion" name="direccion" className="campo-entrada" /></Campo>
                <Campo etiqueta="Usuario" ayuda="Si lo dejas vacío, se usará su número de documento." htmlFor="usuario">
                  <input id="usuario" name="usuario" className="campo-entrada" autoComplete="off" />
                </Campo>
                <Campo etiqueta="Contraseña inicial" obligatorio htmlFor="password">
                  <input id="password" name="password" type="password" minLength={8} required autoComplete="new-password" className="campo-entrada" />
                </Campo>
              </div>
            </div>}

            <div className={formulario.seccion}>
              <div>
                <p className={formulario.seccionTitulo}>Tasa de interés compensatorio</p>
                <p className={formulario.seccionDescripcion}>Es la que se cobra siempre, por el hecho de otorgar el crédito.</p>
              </div>
              <CamposDeTasa sufijo="comp" nombreTasa="tasa_compensatoria" inicial={actual?.tasa_compensatoria} />
            </div>

            <div className={formulario.seccion}>
              <div>
                <p className={formulario.seccionTitulo}>Tasa de interés moratorio</p>
                <p className={formulario.seccionDescripcion}>
                  Se pacta aparte de la compensatoria y solo se aplica si el cliente paga después de su fecha de pago.
                </p>
              </div>
              <CamposDeTasa sufijo="mora" nombreTasa="tasa_moratoria" inicial={actual?.tasa_moratoria} />
            </div>

            <div className={formulario.seccion}>
              <p className={formulario.seccionTitulo}>Condiciones del crédito</p>
              <div className={formulario.rejilla2}>
                <Campo etiqueta="Moneda" obligatorio htmlFor="moneda">
                  <select key={monedas.datos?.length ?? 0} id="moneda" name="moneda" className="campo-entrada" defaultValue={actual?.moneda.codigo_iso ?? 'PEN'}>
                    {(monedas.datos ?? []).map((moneda) => <option key={moneda.codigo_iso} value={moneda.codigo_iso}>{moneda.codigo_iso} ({moneda.simbolo})</option>)}
                  </select>
                </Campo>
                <Campo
                  etiqueta="Límite de crédito"
                  ayuda="Tope de capital pendiente que puede tener este cliente."
                  obligatorio
                  htmlFor="limite_credito"
                >
                  <input
                    id="limite_credito"
                    name="limite_credito"
                    defaultValue={actual?.limite_credito}
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
                  <input id="max_meses" name="max_meses" type="number" defaultValue={actual?.max_meses} min={1} max={120} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Día de corte" ayuda="Día del mes (1 a 28) en que se cierra su período de compras." obligatorio htmlFor="dia_corte">
                  <input id="dia_corte" name="dia_corte" type="number" defaultValue={actual?.dia_corte} min={1} max={28} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
                <Campo etiqueta="Día de pago" ayuda="Día del mes (1 a 28) en que se compromete a pagar." obligatorio htmlFor="dia_pago">
                  <input id="dia_pago" name="dia_pago" type="number" defaultValue={actual?.dia_pago} min={1} max={28} step={1} inputMode="numeric" className="campo-entrada" required />
                </Campo>
              </div>
            </div>

            {clienteCondicion && <p className={formulario.seccionDescripcion}>Los cambios rigen desde {formatearFecha(hoyLima())}.</p>}
            <Campo etiqueta="Hora de corte" ayuda="Hora de Lima." htmlFor="hora_corte">
              <input id="hora_corte" name="hora_corte" type="time" className="campo-entrada" defaultValue={actual?.hora_corte.slice(0, 5) ?? '00:00'} />
            </Campo>
            <div className={formulario.acciones}>
              <Boton variante="secundario" onClick={cerrarModal}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={accion.ocupado || !monedas.datos}>{clienteCondicion ? 'Guardar condiciones' : 'Guardar cliente'}</Boton>
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
  inicial?: TasaPactada
}

/** Los cuatro datos que definen una tasa pactada. La capitalización solo se pide si la tasa es nominal. */
function CamposDeTasa({ sufijo, nombreTasa, inicial }: CamposDeTasaProps) {
  const [tipo, setTipo] = useState<TipoTasa>(inicial?.tipo ?? 'NOMINAL')
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
      <Campo etiqueta="Tasa (%)" ayuda="Mayor que cero. Puedes ingresar hasta 7 decimales." obligatorio htmlFor={nombreTasa}>
        <input
          id={nombreTasa}
          name={nombreTasa}
          type="number"
          step="0.0000001"
          min="0.0000001"
          defaultValue={inicial?.tasa_pct}
          inputMode="decimal"
          className="campo-entrada"
          required
        />
      </Campo>
      <Campo etiqueta="Plazo de la tasa" ayuda="A qué período corresponde la tasa que escribiste." obligatorio htmlFor={idPlazo}>
        <select id={idPlazo} name={idPlazo} className="campo-entrada" defaultValue={inicial?.plazo_dias ?? 360}>
          {[...new Set([...(inicial ? [inicial.plazo_dias] : []), ...PLAZOS])].map((dias) => (
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
          <select id={idCapitalizacion} name={idCapitalizacion} className="campo-entrada" defaultValue={inicial?.capitalizacion_dias ?? CAPITALIZACION_POR_DEFECTO}>
            {[...new Set([...(inicial?.capitalizacion_dias ? [inicial.capitalizacion_dias] : []), ...PLAZOS])].map((dias) => (
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
