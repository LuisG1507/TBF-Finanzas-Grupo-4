import type { ReactNode } from 'react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { RutaProtegida } from './components/RutaProtegida'
import { DatosProvider } from './contexts/DatosContext'
import { SesionProvider } from './contexts/SesionContext'
import { TemaProvider } from './contexts/TemaContext'
import { Clientes } from './pages/AdminNegocio/Clientes'
import { Dashboard } from './pages/AdminNegocio/Dashboard'
import { EstadosCuenta } from './pages/AdminNegocio/EstadosCuenta'
import { NuevaCompra } from './pages/AdminNegocio/NuevaCompra'
import { Productos } from './pages/AdminNegocio/Productos'
import { RegistrarPago } from './pages/AdminNegocio/RegistrarPago'
import { Tiendas } from './pages/AdminSistema/Tiendas'
import { MiCuenta } from './pages/Cliente/MiCuenta'
import { CalculadoraTasas } from './pages/Dev/CalculadoraTasas'
import { Login } from './pages/Login/Login'
import type { RolCodigo } from './types/dominio'

/** Envuelve una pantalla para que solo la vea el rol indicado. */
function soloPara(rol: RolCodigo, pantalla: ReactNode) {
  return <RutaProtegida rolesPermitidos={[rol]}>{pantalla}</RutaProtegida>
}

export default function App() {
  return (
    <TemaProvider>
      <SesionProvider>
        {/* Los datos viven por encima de las rutas: así no se pierden al cambiar de pantalla */}
        <DatosProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />

              {/* Administrador del sistema */}
              <Route path="/admin-sistema/tiendas" element={soloPara('ADMIN_SIS', <Tiendas />)} />

              {/* Administrador del negocio */}
              <Route path="/admin-negocio" element={soloPara('ADMIN_NEG', <Dashboard />)} />
              <Route path="/admin-negocio/productos" element={soloPara('ADMIN_NEG', <Productos />)} />
              <Route path="/admin-negocio/clientes" element={soloPara('ADMIN_NEG', <Clientes />)} />
              <Route path="/admin-negocio/compras/nueva" element={soloPara('ADMIN_NEG', <NuevaCompra />)} />
              <Route path="/admin-negocio/pagos/nuevo" element={soloPara('ADMIN_NEG', <RegistrarPago />)} />
              <Route path="/admin-negocio/estados-cuenta" element={soloPara('ADMIN_NEG', <EstadosCuenta />)} />

              {/* Cliente */}
              <Route path="/cliente/mi-cuenta" element={soloPara('CLIENTE', <MiCuenta />)} />

              {/* Página de pruebas contra el backend real (sin sesión) */}
              <Route path="/dev/calculadora" element={<CalculadoraTasas />} />

              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </Router>
        </DatosProvider>
      </SesionProvider>
    </TemaProvider>
  )
}
