import { useId, useState } from 'react'
import { llamarFinanzas } from '../../api/finanzas'
import { Aviso } from '../../components/ui/Aviso'
import { Boton } from '../../components/ui/Boton'
import { Campo } from '../../components/ui/Campo'
import { Tarjeta, TarjetaEncabezado } from '../../components/ui/Tarjeta'
import styles from './Dev.module.css'

const SIN_CONEXION = 'No se pudo conectar con el backend. ¿Está corriendo «uvicorn app.main:app --reload» en Backend-Grupo4?'

interface BloquePruebaProps {
  titulo: string
  /** El resultado esperado, tomado del material del curso. */
  casoValidado: string
  ruta: string
  ejemplo: object
}

export function BloquePrueba({ titulo, casoValidado, ruta, ejemplo }: BloquePruebaProps) {
  const idCuerpo = useId()
  const [cuerpo, setCuerpo] = useState(JSON.stringify(ejemplo, null, 2))
  const [resultado, setResultado] = useState<string | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function probar() {
    setCargando(true)
    setError(null)
    setResultado(null)

    let json: unknown
    try {
      json = JSON.parse(cuerpo)
    } catch {
      setError('El cuerpo no es un JSON válido. Revisa comas y comillas.')
      setCargando(false)
      return
    }

    try {
      const { ok, estado, datos } = await llamarFinanzas(ruta, json)
      if (!ok && datos === null) {
        // El proxy de Vite contesta con un error sin cuerpo cuando no encuentra al backend.
        setError(SIN_CONEXION)
        return
      }
      setResultado(JSON.stringify(datos, null, 2))
      if (!ok) setError(`El backend rechazó la petición (error ${estado}). El detalle está abajo.`)
    } catch {
      setError(SIN_CONEXION)
    } finally {
      setCargando(false)
    }
  }

  return (
    <Tarjeta>
      <TarjetaEncabezado titulo={titulo} descripcion={casoValidado} accion={<code>POST /api/v1/finanzas/{ruta}</code>} />
      <Campo etiqueta="Cuerpo de la petición (JSON)" ayuda="Puedes cambiar los valores para probar otros casos." htmlFor={idCuerpo}>
        <textarea
          id={idCuerpo}
          className={['campo-entrada', styles.codigo].join(' ')}
          rows={Math.min(12, cuerpo.split('\n').length + 1)}
          spellCheck={false}
          value={cuerpo}
          onChange={(evento) => setCuerpo(evento.target.value)}
        />
      </Campo>

      <div className={styles.acciones}>
        <Boton onClick={probar} disabled={cargando}>
          {cargando ? 'Consultando…' : 'Probar contra el backend'}
        </Boton>
      </div>

      {error && (
        <div className={styles.respuesta}>
          <Aviso tono="peligro">{error}</Aviso>
        </div>
      )}

      {resultado && <pre className={[styles.respuesta, styles.salida].join(' ')}>{resultado}</pre>}
    </Tarjeta>
  )
}
