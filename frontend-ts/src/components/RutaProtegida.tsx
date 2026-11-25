import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSesion } from '../contexts/sesion'
import type { RolCodigo } from '../types/dominio'
import { NAV_POR_ROL } from './layout/navegacion'
import { Aviso } from './ui/Aviso'

export function RutaProtegida({ rolesPermitidos, children }: { rolesPermitidos: RolCodigo[]; children: ReactNode }) {
  const { sesion, verificando } = useSesion()
  if (verificando) return <Aviso tono="info">Verificando sesión…</Aviso>
  if (!sesion) return <Navigate to="/login" replace />
  if (!rolesPermitidos.includes(sesion.rol)) return <Navigate to={NAV_POR_ROL[sesion.rol][0].ruta} replace />
  return <>{children}</>
}
