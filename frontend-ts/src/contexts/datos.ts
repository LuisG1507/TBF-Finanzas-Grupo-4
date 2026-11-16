import { createContext, useContext } from 'react'
import type { Cliente, Producto, Tienda } from '../types/dominio'

/*
  Los datos que varias pantallas comparten mientras la aplicación no esté conectada al backend.
  Antes cada pantalla cargaba su propia copia de data/mock.ts, así que un cliente nuevo solo
  existía dentro de la pantalla de Clientes. Ahora todas leen y escriben aquí.

  Cuando existan los endpoints de negocio, este es el único lugar que cambia: las funciones
  agregar… pasarán a llamar al backend y las pantallas seguirán igual.
*/
export interface DatosContextValor {
  tiendas: Tienda[]
  productos: Producto[]
  clientes: Cliente[]
  agregarTienda: (tienda: Tienda) => void
  /** Da de baja una tienda activa o reactiva una dada de baja. */
  alternarTienda: (idTienda: number) => void
  agregarProducto: (producto: Producto) => void
  agregarCliente: (cliente: Cliente) => void
}

export const DatosContext = createContext<DatosContextValor | null>(null)

export function useDatos(): DatosContextValor {
  const contexto = useContext(DatosContext)
  if (!contexto) throw new Error('useDatos debe usarse dentro de DatosProvider')
  return contexto
}

/** El siguiente identificador libre de una lista (lo asignará la base de datos cuando haya backend). */
export function siguienteId(ids: number[]): number {
  return Math.max(0, ...ids) + 1
}
