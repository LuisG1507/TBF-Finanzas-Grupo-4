import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { clientesDemo, productosDemo, tiendasDemo } from '../data/mock'
import type { Cliente, Producto, Tienda } from '../types/dominio'
import { DatosContext } from './datos'

/*
  Guarda en memoria las tiendas, los productos y los clientes, partiendo de los datos de muestra.
  Lo que se agrega vive mientras la página esté abierta: al recargar se vuelve a los datos de muestra,
  porque todavía no se guarda nada en la base de datos.
*/
export function DatosProvider({ children }: { children: ReactNode }) {
  const [tiendas, setTiendas] = useState<Tienda[]>(tiendasDemo)
  const [productos, setProductos] = useState<Producto[]>(productosDemo)
  const [clientes, setClientes] = useState<Cliente[]>(clientesDemo)

  const agregarTienda = useCallback((tienda: Tienda) => setTiendas((actuales) => [tienda, ...actuales]), [])

  const alternarTienda = useCallback((idTienda: number) => {
    setTiendas((actuales) =>
      actuales.map((tienda) => (tienda.id_tienda === idTienda ? { ...tienda, activo: !tienda.activo } : tienda)),
    )
  }, [])

  const agregarProducto = useCallback((producto: Producto) => setProductos((actuales) => [producto, ...actuales]), [])

  const agregarCliente = useCallback((cliente: Cliente) => setClientes((actuales) => [cliente, ...actuales]), [])

  const valor = useMemo(
    () => ({ tiendas, productos, clientes, agregarTienda, alternarTienda, agregarProducto, agregarCliente }),
    [tiendas, productos, clientes, agregarTienda, alternarTienda, agregarProducto, agregarCliente],
  )

  return <DatosContext.Provider value={valor}>{children}</DatosContext.Provider>
}
