import type { RolCodigo } from '../../types/dominio'
import type { NombreIcono } from '../ui/Icono'

export interface ItemNav {
  ruta: string
  etiqueta: string
  icono: NombreIcono
  /** true = solo se marca como activo si la ruta coincide exacta (para la página de inicio del rol). */
  fin?: boolean
}

/** El menú de cada rol. Las rutas son las mismas que protege App.tsx. */
export const NAV_POR_ROL: Record<RolCodigo, ItemNav[]> = {
  ADMIN_SIS: [{ ruta: '/admin-sistema/tiendas', etiqueta: 'Tiendas', icono: 'tienda' }],
  ADMIN_NEG: [
    { ruta: '/admin-negocio', etiqueta: 'Resumen', icono: 'tablero', fin: true },
    { ruta: '/admin-negocio/productos', etiqueta: 'Productos', icono: 'caja' },
    { ruta: '/admin-negocio/clientes', etiqueta: 'Clientes', icono: 'personas' },
    { ruta: '/admin-negocio/compras/nueva', etiqueta: 'Nueva compra', icono: 'bolsa' },
    { ruta: '/admin-negocio/pagos/nuevo', etiqueta: 'Registrar pago', icono: 'billete' },
    { ruta: '/admin-negocio/estados-cuenta', etiqueta: 'Estados de cuenta', icono: 'documento' },
  ],
  CLIENTE: [{ ruta: '/cliente/mi-cuenta', etiqueta: 'Mi cuenta', icono: 'usuario' }],
}

export const NOMBRE_ROL: Record<RolCodigo, string> = {
  ADMIN_SIS: 'Administrador del sistema',
  ADMIN_NEG: 'Administrador del negocio',
  CLIENTE: 'Cliente',
}

export const NOMBRE_APLICACION = 'Créditos de barrio'
