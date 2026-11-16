export async function llamarFinanzas(ruta: string, cuerpo: unknown): Promise<{ ok: boolean; estado: number; datos: unknown }> {
  const respuesta = await fetch(`/api/v1/finanzas/${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  })
  const datos = await respuesta.json().catch(() => null)
  return { ok: respuesta.ok, estado: respuesta.status, datos }
}
