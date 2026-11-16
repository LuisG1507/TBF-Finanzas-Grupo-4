# TBF — Frontend (experimental, Grupo 4)

> **Nota:** esto es una exploración personal, no la entrega oficial del grupo para el Hito 1.
> Las pantallas oficiales las está armando el resto del equipo. Esta carpeta sirve como
> referencia de una posible dirección de diseño (y como prueba de que el motor financiero del
> backend funciona conectado a una interfaz real), no reemplaza ese trabajo.

Diseño de interfaz para el Hito 1 de SI642: las pantallas con las que el usuario va a interactuar
con el sistema, cada campo con su ayuda contextual (requisito explícito del enunciado, punto 6b).

## Stack

React + TypeScript + Vite, sin librerías de UI externas (CSS propio, con módulos CSS por
componente, estilo inspirado en las interfaces de Apple). React Router para la navegación.

## Cómo correrlo

```bash
npm install
npm run dev
```

Abre `http://localhost:5173/login`. Elige un "Perfil de acceso" (Admin. del sistema, Admin.
del negocio o Cliente) para ver las pantallas de cada rol — no hay backend de autenticación
todavía, así que el selector de perfil es explícitamente parte de esta demo, no del sistema
final.

## Estructura

```
src/
  types/dominio.ts       tipos que reflejan 1 a 1 los modelos de Backend-Grupo4
  data/mock.ts            datos de muestra para las pantallas de diseño
  contexts/SesionContext  quién inició sesión y con qué rol (solo para esta demo)
  components/ui/          piezas reutilizables: Boton, Campo, Tarjeta, Insignia, Modal...
  components/layout/      BarraLateral (nav por rol) y Shell (marco de cada pantalla)
  pages/
    Login/
    AdminSistema/          alta y baja de tiendas
    AdminNegocio/          resumen, productos, clientes, nueva compra, pagos, estados de cuenta
    Cliente/               consulta de su propio estado de cuenta
    Dev/                   ver más abajo
```

## La pieza que cumple el requisito de ayuda contextual

`components/ui/Campo.tsx` envuelve cada campo de cada formulario con una etiqueta y un texto
de ayuda (con su ícono). Es el mismo componente en las ~40 entradas de todo el proyecto, así
que basta con darle `ayuda="..."` a cualquier campo nuevo para cumplir el requisito.

## `pages/Dev/CalculadoraTasas` — la única pantalla conectada al backend real

El resto de la aplicación usa `data/mock.ts` (datos de muestra locales), porque para el
Hito 1 solo se pide el **diseño** de las pantallas. Pero como el motor financiero
(`app/services/finance/finance_tasas.py` en `Backend-Grupo4`) ya existe y está probado, esta
página aparte llama de verdad a `POST /api/v1/finanzas/...` para demostrar que el diseño de
los datos (`types/dominio.ts`) coincide con lo que el backend realmente devuelve.

Para probarla:

1. Backend (desde la carpeta de arriba, `Backend-Grupo4`): `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`
2. Frontend: `npm run dev` (el `vite.config.ts` ya tiene un proxy de `/api` hacia
   `http://127.0.0.1:8000`, así que no hay problema de CORS)
3. Abre `http://localhost:5173/dev/calculadora`

Si el backend no está corriendo, el bloque de prueba lo indica con un mensaje claro en vez de
fallar en silencio.
