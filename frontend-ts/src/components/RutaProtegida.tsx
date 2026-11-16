import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSesion } from '../contexts/sesion'
import type { RolCodigo } from '../types/dominio'

export function RutaProtegida({ rolesPermitidos, children }: { rolesPermitidos: RolCodigo[]; children: ReactNode }) {
  const { sesion } = useSesion()
  if (!sesion) return <Navigate to="/login" replace />
  if (!rolesPermitidos.includes(sesion.rol)) return <Navigate to="/login" replace />
  return <>{children}</>
}
