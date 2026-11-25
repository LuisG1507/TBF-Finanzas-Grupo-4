# Frontend de Bizon

Interfaz React y TypeScript con Vite. Los formularios y las consultas usan Bizon API. Tras iniciar sesión, cada rol accede a las pantallas que le corresponden.

Con el backend levantado, instala las dependencias desde esta carpeta y abre Bizon.

```powershell
npm ci
npm run dev
```

Vite sirve la aplicación en `http://localhost:5173` y redirige `/api` al backend local en el puerto 8000. Define `TBF_API_PROXY` para utilizar otra dirección en desarrollo.

Ejecuta `npm run build` para generar `dist` y `npm run lint` para revisar el código. La calculadora de apoyo en `/dev/calculadora` solo está disponible en desarrollo.

[Guía de instalación, cuentas demo y pruebas](../README.md)
