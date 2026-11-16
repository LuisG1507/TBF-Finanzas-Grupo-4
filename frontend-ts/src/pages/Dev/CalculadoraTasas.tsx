import { Link } from 'react-router-dom'
import { SelectorTema } from '../../components/ui/SelectorTema'
import { BloquePrueba } from './BloquePrueba'
import styles from './Dev.module.css'

/*
  Página de pruebas contra el backend real (FastAPI). No usa datos de muestra:
  cada botón llama al servidor de Backend-Grupo4 a través del proxy /api de Vite.
*/
export function CalculadoraTasas() {
  return (
    <div className={styles.pagina}>
      <header className={styles.encabezado}>
        <div>
          <p className={styles.antetitulo}>Pruebas funcionales</p>
          <h1 className={styles.titulo}>Motor financiero real</h1>
          <p className={styles.subtitulo}>
            Verifica en vivo que el backend responde igual que en Swagger. Cada bloque llama a <code>/api/v1/finanzas</code>; el resto de la
            aplicación todavía usa datos de muestra. <Link to="/login">Volver al inicio de sesión</Link>
          </p>
        </div>
        <SelectorTema />
      </header>

      <BloquePrueba
        titulo="Método francés con días de gracia"
        casoValidado="S/ 1,000 a TNA 24 % capitalizable mensualmente, 3 cuotas y 11 días de gracia → capital S/ 1,007.29 y cuota S/ 349.28."
        ruta="frances"
        ejemplo={{
          capital: 1000,
          tipo_tasa: 'NOMINAL',
          tasa_pct: 24,
          plazo_tasa: 'ANUAL',
          capitalizacion: 'MENSUAL',
          periodo_pago: 'MENSUAL',
          num_cuotas: 3,
          dias_gracia: 11,
        }}
      />

      <BloquePrueba
        titulo="Interés compuesto: monto"
        casoValidado="S/ 50,000 al 8 % anual con capitalización diaria durante 236 días → S/ 52,691.89."
        ruta="compuesto/monto"
        ejemplo={{
          plazo_tasa: 'ANUAL',
          capitalizacion: 'DIARIA',
          tasa_nominal_pct: 8,
          plazo: 236,
          unidad_plazo: 'DIAS',
          capital: 50000,
        }}
      />

      <BloquePrueba
        titulo="Interés simple: interés"
        casoValidado="El mismo caso en régimen simple → S/ 2,622.22."
        ruta="simple/interes"
        ejemplo={{
          capital: 50000,
          tasa_pct: 8,
          plazo_tasa: 'ANUAL',
          plazo: 236,
          unidad_plazo: 'DIAS',
        }}
      />

      <BloquePrueba
        titulo="Conversión de tasas"
        casoValidado="TEM 4 % a TNA capitalizable diariamente (ejercicio 4 del material del curso) → 47.0956345 %."
        ruta="conversion-tasas"
        ejemplo={{
          tipo_origen: 'EFECTIVA',
          tasa_pct: 4,
          plazo_origen: 'MENSUAL',
          tipo_destino: 'NOMINAL',
          plazo_destino: 'ANUAL',
          capitalizacion_destino: 'DIARIA',
        }}
      />
    </div>
  )
}
