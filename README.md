# Bizon

Bizon gestiona el crédito de los negocios de barrio. El administrador del sistema registra tiendas. Cada administrador de negocio gestiona sus productos, clientes, compras, estados de cuenta y pagos. Los clientes consultan su propio crédito, compras y estados.

## Requisitos locales

- Python 3.13 y PostgreSQL disponibles. Crea una base vacía y usa una cuenta de PostgreSQL con permisos para aplicar migraciones. Las pruebas de integración necesitan además crear y retirar esquemas temporales.
- Node.js 20 desde la versión 20.19, o Node.js 22.12 en adelante, y npm. Para la prueba de navegador, instala Chrome o indica su ejecutable con `TBF_NAVEGADOR`.

## 1. Backend

Desde la raíz del repositorio en PowerShell, prepara el entorno virtual e instala las dependencias.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si aún falta `.env`, copia `.env.example` y ajusta `URL_BASE_DATOS`, `CLAVE_SECRETA`, `ADMIN_SISTEMA_USUARIO` y `ADMIN_SISTEMA_PASSWORD`. Guarda las credenciales únicamente en tu archivo local. Aplica las migraciones, carga los catálogos y el administrador inicial, y levanta la API.

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m app.db.seeds
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La API escucha en el puerto 8000. Los datos iniciales pueden cargarse más de una vez. [Swagger de Bizon](http://127.0.0.1:8000/docs)

## 2. Frontend

Abre otra terminal en la raíz del repositorio y ejecuta estos comandos.

```powershell
Set-Location frontend-ts
npm ci
npm run dev
```

Ingresa con el administrador del sistema configurado en `.env`. Da de alta una tienda y define las credenciales de su administrador. Las cuentas de cliente se crean desde el módulo **Clientes** de cada tienda. [Inicio de sesión local](http://localhost:5173/login)

Vite redirige `/api` a `http://127.0.0.1:8000` en desarrollo. Si la API usa otro puerto, define `TBF_API_PROXY` antes de arrancar Vite. `npm run build` genera `frontend-ts/dist`. Al servir esa compilación, publica `/api/v1` en el mismo origen y configura el retorno a `index.html` para las rutas de React. `/dev/calculadora` está disponible en desarrollo para revisar el motor financiero.

## 3. Demo de Bodega Don Rosendo

Con el administrador del sistema, crea una tienda activa con el nombre comercial **Bodega Don Rosendo**. Desde la raíz del repositorio, carga la demo.

```powershell
.venv\Scripts\python.exe -m app.db.demo
```

La demo incluye seis productos, nueve clientes y operaciones de setiembre a noviembre de 2026. Usa `demo.ana` para consultar un cronograma, `demo.jorge` para ver un pago con mora y `demo.elena` para ver una cuenta en dólares. Esas cuentas de demostración usan la contraseña `DonRosendo26`.

Para retirar la demo, ejecuta el siguiente comando. Si una operación ingresada después depende de la demo, Bizon conserva los datos y comunica el conflicto.

```powershell
.venv\Scripts\python.exe -m app.db.demo --limpiar
```

## 4. Pruebas

Desde la raíz del repositorio, ejecuta las pruebas de integración. Cada una levanta su propia API, usa un esquema PostgreSQL temporal y lo retira al terminar. La prueba de Chrome inicia también su propio servidor Vite.

```powershell
.venv\Scripts\python.exe -m datos_prueba.pruebas_http.flujo_completo
.venv\Scripts\python.exe -m datos_prueba.pruebas_http.bloque_a
.venv\Scripts\python.exe -m datos_prueba.pruebas_http.frontend_real
```

El flujo completo aplica las migraciones desde cero y recorre los tres roles. Incluye la compra del 15 de setiembre, el corte del 20, el cronograma francés, el pago puntual, el pago tardío y la consulta del titular.

Con la API local levantada, también puedes contrastar los 29 ejercicios de clase y los dos casos de TCEA con este comando.

```powershell
.venv\Scripts\python.exe datos_prueba\verificar_casos.py
```

Desde `frontend-ts`, comprueba la compilación y el análisis de código con `npm run build` y `npm run lint`.

## Demo desplegada

El `Dockerfile` compila React y arranca la API con `app.web:app`. El frontend y `/api/v1` salen del mismo dominio. La comprobación de arranque está en `/healthz`. El proceso escucha en el puerto que indique `PORT`, con 8000 como valor inicial.

Configura una base PostgreSQL de prueba en `URL_BASE_DATOS` y define `CLAVE_SECRETA`, `ADMIN_SISTEMA_USUARIO` y `ADMIN_SISTEMA_PASSWORD` como variables del servicio. Desde la imagen, ejecuta `python -m alembic upgrade head` y `python -m app.db.seeds` una vez al preparar la base. Después usa el administrador del sistema para crear las tiendas de prueba y asignar una cuenta de administrador a cada participante. Si creas **Bodega Don Rosendo**, `python -m app.db.demo` carga la historia y las cuentas de cliente descritas arriba.
