import type { ReactNode, SVGAttributes } from 'react'

/*
  Íconos propios, dibujados a mano sobre una rejilla de 24 × 24 con trazo redondeado.
  Para agregar uno nuevo basta con sumar su entrada a TRAZOS.
*/
const TRAZOS = {
  tablero: (
    <>
      <rect x="3.5" y="3.5" width="7" height="9" rx="2" />
      <rect x="13.5" y="3.5" width="7" height="5" rx="2" />
      <rect x="13.5" y="11.5" width="7" height="9" rx="2" />
      <rect x="3.5" y="15.5" width="7" height="5" rx="2" />
    </>
  ),
  tienda: (
    <>
      <path d="M4 9.5 5.3 4.5h13.4L20 9.5" />
      <path d="M4 9.5a2.67 2.67 0 0 0 5.33 0 2.67 2.67 0 0 0 5.34 0 2.67 2.67 0 0 0 5.33 0" />
      <path d="M5.5 12.5v7h13v-7" />
      <path d="M10 19.5v-4h4v4" />
    </>
  ),
  caja: (
    <>
      <path d="M12 3.2 20 7.4v9.2L12 20.8 4 16.6V7.4L12 3.2Z" />
      <path d="M4 7.4 12 11.6l8-4.2" />
      <path d="M12 11.6v9.2" />
    </>
  ),
  personas: (
    <>
      <circle cx="9" cy="8.5" r="3.2" />
      <path d="M3.5 19.5c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5" />
      <path d="M15.3 5.7a2.8 2.8 0 0 1 0 5.4" />
      <path d="M17 14.8c1.9.5 3.1 2 3.5 4.7" />
    </>
  ),
  bolsa: (
    <>
      <path d="M5.6 8.5h12.8l1 11.5H4.6l1-11.5Z" />
      <path d="M9 8.5V7a3 3 0 0 1 6 0v1.5" />
      <path d="M12 12.2v4.4M9.8 14.4h4.4" />
    </>
  ),
  billete: (
    <>
      <rect x="3" y="6.5" width="18" height="11" rx="2.6" />
      <circle cx="12" cy="12" r="2.6" />
      <path d="M6.6 12h.01M17.4 12h.01" />
    </>
  ),
  documento: (
    <>
      <path d="M7 3.5h7L18.5 8v11a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z" />
      <path d="M14 3.5V8h4.5" />
      <path d="M8.8 12.5h6.4M8.8 16h4" />
    </>
  ),
  usuario: (
    <>
      <circle cx="12" cy="8.5" r="3.6" />
      <path d="M5 19.5c.8-3.4 3.5-5.2 7-5.2s6.2 1.8 7 5.2" />
    </>
  ),
  sol: (
    <>
      <circle cx="12" cy="12" r="3.8" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4" />
    </>
  ),
  luna: <path d="M20 14.3A8 8 0 0 1 9.7 4a8 8 0 1 0 10.3 10.3Z" />,
  automatico: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 3.5a8.5 8.5 0 0 1 0 17v-17Z" fill="currentColor" stroke="none" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  cerrar: <path d="M6 6l12 12M18 6 6 18" />,
  salir: (
    <>
      <path d="M10 4.5H6.5A1.5 1.5 0 0 0 5 6v12a1.5 1.5 0 0 0 1.5 1.5H10" />
      <path d="M14.5 8l4 4-4 4M18.5 12H9.5" />
    </>
  ),
  mas: <path d="M12 5v14M5 12h14" />,
  sube: <path d="M7.5 16.5 16.5 7.5M9.5 7.5h7v7" />,
  baja: <path d="M7.5 7.5l9 9M16.5 9.5v7h-7" />,
  chevronAbajo: <path d="M6 9.5l6 6 6-6" />,
  chevronDerecha: <path d="M9.5 6l6 6-6 6" />,
  info: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),
  alerta: (
    <>
      <path d="M12 4.2 20.8 19.5H3.2L12 4.2Z" />
      <path d="M12 10.2v4.3M12 17h.01" />
    </>
  ),
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  calendario: (
    <>
      <rect x="4" y="5.5" width="16" height="14.5" rx="2.6" />
      <path d="M4 10h16M8.5 3.5v4M15.5 3.5v4" />
    </>
  ),
  tabla: (
    <>
      <rect x="3.5" y="5" width="17" height="14" rx="2.6" />
      <path d="M3.5 10h17M3.5 14.5h17M9.5 10v9" />
    </>
  ),
  barras: <path d="M5.5 19.5v-6M10 19.5V5.5M14.5 19.5v-9M19 19.5v-4" />,
  candado: (
    <>
      <rect x="5.5" y="10.5" width="13" height="9.5" rx="2.6" />
      <path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" />
    </>
  ),
  reloj: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </>
  ),
  buscar: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16l4 4" />
    </>
  ),
  cuaderno: (
    <>
      <rect x="5.5" y="3.5" width="13.5" height="17" rx="2.6" />
      <path d="M9 3.5v17" />
      <path d="M12 9.5l1.8 1.8 3-3.3M12.2 15.5h4.3" />
    </>
  ),
} satisfies Record<string, ReactNode>

export type NombreIcono = keyof typeof TRAZOS

interface IconoProps extends Omit<SVGAttributes<SVGSVGElement>, 'children'> {
  nombre: NombreIcono
  tamano?: number
  grosor?: number
}

export function Icono({ nombre, tamano = 20, grosor = 1.75, ...resto }: IconoProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={tamano}
      height={tamano}
      fill="none"
      stroke="currentColor"
      strokeWidth={grosor}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...resto}
    >
      {TRAZOS[nombre]}
    </svg>
  )
}
