# Juegos de datos de prueba

Material para el punto 6d del informe (*Diseño de Datos de prueba*: «por lo menos 2 juegos de datos de prueba, los que permitan comprobar la veracidad del modelo desarrollado»). Dos juegos con los que se comprueba el motor financiero (`app/services/finance/`). Cada cifra del sistema se obtuvo llamando a la API real (`POST /api/v1/finanzas/frances`); cada cifra de la clase, del Excel del curso. Se pueden volver a correr con `datos_prueba/verificar_casos.py`.

**Convenciones (Anexo A):** año de 360 días y mes de 30 días; montos a 2 decimales; tasas a 7 decimales; `Decimal` en todo cálculo.

**Nota de redondeo.** El cronograma se calcula con los montos ya redondeados a 2 decimales, así que **cada fila cuadra**: interés + amortización = cuota, saldo inicial − amortización = saldo final, y el saldo final de una fila es el saldo inicial de la siguiente. La cuota fija se calcula con la fórmula completa y se redondea al final; la **última cuota** se ajusta (amortiza todo el saldo que queda) y absorbe los céntimos de redondeo. Por eso la última cuota puede diferir de las demás en unos céntimos, y el total a pagar es exactamente capital capitalizado + intereses. El Excel de clase no redondea y muestra los valores completos; las diferencias contra el Excel son de céntimos.

**Fórmulas usadas** (método francés con período de gracia capitalizado):

| Paso | Fórmula |
|---|---|
| Tasa nominal → tasa efectiva del período | `TEP = (1 + TN/m)^n − 1`, con `m` = plazo de la tasa ÷ días de capitalización y `n` = días del período de pago ÷ días de capitalización |
| Tasa efectiva → tasa efectiva del período | `TEP = (1 + TE)^(días del período de pago ÷ plazo de la tasa) − 1` |
| Capitalización de la gracia | `C' = C · (1 + TEP)^(días de gracia ÷ días del período de pago)` |
| Cuota fija | `R = C' · TEP · (1 + TEP)^n / ((1 + TEP)^n − 1)` |
| Cada período | `I = TEP · saldo inicial`, `A = R − I`, `saldo final = saldo inicial − A` |

## Juego 1 — Ejemplo del enunciado (compra con 11 días de gracia)

**Escenario (enunciado, punto 4).** Pago en 3 meses, fecha de pago los 26 de cada mes; la compra se hace el 15 de setiembre, antes de la fecha de corte (20 de setiembre). Entre el 15 y el 26 de setiembre hay **11 días de período de gracia total**, por lo que la deuda se capitaliza antes de calcular la cuota. Las cuotas vencen el 26 de octubre, el 26 de noviembre y el 26 de diciembre. El enunciado no fija monto ni tasa: S/ 1,000.00 y TNA 24 % son los del caso que el equipo usa para validar el motor.

### Datos de entrada

| Campo | Valor |
|---|---|
| Capital financiado `C` | S/ 1,000.00 |
| Tasa | 24 % nominal anual (TNA), capitalización mensual |
| Plazo de la tasa / capitalización | 360 días / 30 días |
| Período de pago | mensual (30 días) |
| Número de cuotas `n` | 3 |
| Días de gracia | 11 |

### Datos intermedios (paso a paso)

| Dato | Cálculo | Sistema |
|---|---|---|
| `m` | 360 ÷ 30 | 12 |
| `n` del período | 30 ÷ 30 | 1 |
| TEP | (1 + 0.24/12)^1 − 1 | 2.0000000 % |
| Capital capitalizado `C'` | 1,000.00 · (1.02)^(11/30) | S/ 1,007.29 |
| Interés de la gracia | `C' − C` | S/ 7.29 |
| Cuota `R` | `C'·TEP·(1+TEP)^3 / ((1+TEP)^3 − 1)` | S/ 349.28 |

Verificación independiente (cálculo directo en `Decimal`, sin pasar por la API): TEP = 2.0000000 %, C' = 1,007.29, R = 349.28.

### Resultado: cronograma

| N° | Vence | Saldo inicial | Interés | Amortización | Cuota | Saldo final |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 26 de octubre | 1,007.29 | 20.15 | 329.13 | 349.28 | 678.16 |
| 2 | 26 de noviembre | 678.16 | 13.56 | 335.72 | 349.28 | 342.44 |
| 3 | 26 de diciembre | 342.44 | 6.85 | 342.44 | 349.29 | 0.00 |
| **Total** | | | **40.56** | | **1,047.85** | |

**Resultado esperado:** `C'` = 1,007.29; cuota = 349.28; interés total = 40.56; total a pagar = 1,007.29 + 40.56 = 1,047.85. Sin redondear, el cálculo exacto da `C'` = 1,007.2874, cuota = 349.2816 y total = 1,047.8448 (1,047.84); al trabajar a céntimos la última cuota sube a 349.29 y el total queda 1 céntimo por exceso. **Coincide.**

## Juego 2 — Ejercicio de clase: financiamiento de un terreno (Caso 3 Francés)

**Fuente.** `06 - 01 Clase de Cronograma de Pago (resuelto)`, hoja *Caso 3 Francés* (la misma operación aparece en la diapositiva de método francés). Terreno de S/ 1,800,000 con cuota inicial de 20 % → se financian **S/ 1,440,000** a 4 años, pagos semestrales, **TEA 9 %**. Se prueba sin gracia (2A) y con un semestre de gracia (2B).

### Datos de entrada

| Campo | 2A (sin gracia) | 2B (con gracia) |
|---|---|---|
| Capital financiado `C` | S/ 1,440,000.00 | S/ 1,440,000.00 |
| Tasa | 9 % efectiva anual (TEA) | 9 % efectiva anual (TEA) |
| Período de pago | semestral (180 días) | semestral (180 días) |
| Número de cuotas | 8 | 7 |
| Días de gracia | 0 | 180 (1 semestre) |

### 2A — Sin gracia: cronograma de 8 semestres, sistema contra Excel

TEP = (1 + 0.09)^(180/360) − 1 = **4.4030651 %** (Excel: 4.4030651 %). Cuota = **S/ 217,454.11** (Excel: S/ 217,454.11).

| N° | Saldo inicial | Interés | Amortización | Cuota | Saldo final | Dif. máx. con Excel |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,440,000.00 | 63,404.14 | 154,049.97 | 217,454.11 | 1,285,950.03 | 0.0063 |
| 2 | 1,285,950.03 | 56,621.22 | 160,832.89 | 217,454.11 | 1,125,117.14 | 0.0134 |
| 3 | 1,125,117.14 | 49,539.64 | 167,914.47 | 217,454.11 | 957,202.67 | 0.0176 |
| 4 | 957,202.67 | 42,146.26 | 175,307.85 | 217,454.11 | 781,894.82 | 0.0254 |
| 5 | 781,894.82 | 34,427.34 | 183,026.77 | 217,454.11 | 598,868.05 | 0.0323 |
| 6 | 598,868.05 | 26,368.55 | 191,085.56 | 217,454.11 | 407,782.49 | 0.0373 |
| 7 | 407,782.49 | 17,954.93 | 199,499.18 | 217,454.11 | 208,283.31 | 0.0441 |
| 8 | 208,283.31 | 9,170.85 | 208,283.31 | 217,454.16 | 0.00 | 0.0464 |
| **Total** | | **299,632.93** | | **1,739,632.93** | | |

**Excel:** interés total S/ 299,632.91; total a pagar S/ 1,739,632.91. Diferencia: 0.0210 y 0.0210. La mayor diferencia en toda la tabla es 0.0464, en la última cuota, que absorbe el redondeo acumulado (el Excel no redondea; el sistema trabaja a céntimos).

### 2B — Con un semestre de gracia: 7 cuotas, sistema contra Excel

Capital capitalizado `C'` = 1,440,000.00 · (1.09)^(180/180) = **S/ 1,503,404.14** (Excel: S/ 1,503,404.14). Interés de la gracia: S/ 63,404.14. Cuota = **S/ 254,225.60** (Excel: S/ 254,225.60).

| N° | Saldo inicial | Interés | Amortización | Cuota | Saldo final | Dif. máx. con Excel |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,503,404.14 | 66,195.86 | 188,029.74 | 254,225.60 | 1,315,374.40 | 0.0045 |
| 2 | 1,315,374.40 | 57,916.79 | 196,308.81 | 254,225.60 | 1,119,065.59 | 0.0046 |
| 3 | 1,119,065.59 | 49,273.19 | 204,952.41 | 254,225.60 | 914,113.18 | 0.0046 |
| 4 | 914,113.18 | 40,249.00 | 213,976.60 | 254,225.60 | 700,136.58 | — |
| 5 | 700,136.58 | 30,827.47 | 223,398.13 | 254,225.60 | 476,738.45 | — |
| 6 | 476,738.45 | 20,991.10 | 233,234.50 | 254,225.60 | 243,503.95 | — |
| 7 | 243,503.95 | 10,721.64 | 243,503.95 | 254,225.59 | 0.00 | — |
| **Total** | | **276,175.05** | | **1,779,579.19** | | |

> **Por qué solo se comparan 3 filas.** En el Excel, desde el semestre 5 la tasa baja a TEA 8 % y la cuota se recalcula sobre el saldo. En nuestro sistema cada compra conserva la tasa con la que se hizo (`Compra.condicion_id` congela las condiciones), así que el cronograma sigue con la tasa del 9 %. Las filas 4 a 7 no son comparables. El tramo con la tasa de 8 % se comprobó aparte, como un crédito independiente (ejercicio FR-04 de `casos_clase.json`: cuota S/ 251,372.54).

Mayor diferencia en las 3 filas comparables: 0.0046.

## Cómo repetirlo

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app
.venv\Scripts\python.exe datos_prueba\verificar_casos.py --solo FR-02 FR-03
```

`verificar_casos.py` sin argumentos corre los 29 ejercicios de clase (69 valores) y termina con código 1 si alguno no coincide.
