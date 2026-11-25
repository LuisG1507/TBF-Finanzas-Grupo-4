"""Ciclo de crédito de una compra: a qué corte pertenece, cuándo se paga y cuántos días de gracia hay.
Son funciones puras (sin base de datos ni FastAPI), así que se pueden probar solas.

Reglas (enunciado, puntos 4 y 5, y decisiones del equipo):

1. FECHA DE CORTE. Una compra hecha ANTES de la fecha y hora de corte pertenece al corte de ese mes. Una compra hecha
   en el momento exacto del corte o después, pertenece al corte del mes siguiente (decisión 5: «el mismo día del
   corte, se trata como después del corte»).
2. FECHA DE PAGO DEL CICLO = el primer «día de pago» que cae DESPUÉS de la fecha de corte. Con corte el 20 y pago el
   26, es el 26 del mismo mes; con corte el 25 y pago el 10, es el 10 del mes siguiente.
3. DÍAS DE GRACIA = días entre la fecha de la compra y la fecha de pago del ciclo, con meses de 30 días (30E/360).
   Ejemplo del enunciado: compra el 15 de setiembre y pago el 26 de setiembre = 11 días.
4. CUOTAS. Las cuotas reales empiezan el mes siguiente a la fecha de pago del ciclo (26 de octubre, 26 de noviembre,
   26 de diciembre...).

Los días de corte y de pago van de 1 a 28, así que siempre existen en cualquier mes.
"""
from datetime import date, datetime, time


def sumar_meses(fecha: date, meses: int) -> date:
    """Mismo día, `meses` meses después (o antes si es negativo). Válido porque los días de corte y pago son <= 28."""
    indice = fecha.year * 12 + (fecha.month - 1) + meses
    return fecha.replace(year=indice // 12, month=indice % 12 + 1)


def fecha_corte_asignada(fecha_hora_compra: datetime, dia_corte: int, hora_corte: time) -> date:
    """Fecha de corte del ciclo al que pertenece la compra. `fecha_hora_compra` va en hora local de Lima, sin zona."""
    corte_de_este_mes = fecha_hora_compra.date().replace(day=dia_corte)
    momento_de_corte = datetime.combine(corte_de_este_mes, hora_corte)
    return corte_de_este_mes if fecha_hora_compra < momento_de_corte else sumar_meses(corte_de_este_mes, 1)


def fecha_pago_del_ciclo(fecha_corte: date, dia_pago: int) -> date:
    """Primer día de pago estrictamente posterior a la fecha de corte."""
    candidata = fecha_corte.replace(day=dia_pago)
    return candidata if candidata > fecha_corte else sumar_meses(candidata, 1)


def dias_30_360(desde: date, hasta: date) -> int:
    """Días entre dos fechas con meses de 30 días y año de 360 (base 30E/360): el día 31 cuenta como 30."""
    return (hasta.year - desde.year) * 360 + (hasta.month - desde.month) * 30 + (min(hasta.day, 30) - min(desde.day, 30))


def fechas_de_cuotas(fecha_pago_ciclo: date, num_cuotas: int) -> list[date]:
    """La primera cuota vence un mes después de la fecha de pago del ciclo; las demás, de mes en mes."""
    return [sumar_meses(fecha_pago_ciclo, k) for k in range(1, num_cuotas + 1)]
