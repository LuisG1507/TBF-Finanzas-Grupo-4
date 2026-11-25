/** Quita tildes y pasa a minúsculas, para comparar texto sin que "Ramírez" y "ramirez" sean distintos. */
function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
}

/** true si la consulta aparece en alguno de los textos. Una consulta vacía coincide con todo. */
export function coincide(consulta: string, ...textos: (string | null | undefined)[]): boolean {
  const buscada = normalizar(consulta.trim())
  if (!buscada) return true
  return textos.some((texto) => texto != null && normalizar(texto).includes(buscada))
}

export function nombreCompleto(cliente: { nombres: string; apellidos: string }): string {
  return `${cliente.nombres} ${cliente.apellidos}`
}
