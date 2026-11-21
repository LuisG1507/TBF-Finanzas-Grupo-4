"""Fecha y hora de Lima. El servidor puede estar en otra zona horaria (por ejemplo UTC al desplegar), pero el
negocio vive en Perú: la fecha de «hoy» y la hora de corte se miden en hora de Lima.
Perú no tiene horario de verano, así que basta un desfase fijo de -5 horas (no hace falta la base `tzdata`)."""
from datetime import date, datetime, timedelta, timezone

ZONA_LIMA = timezone(timedelta(hours=-5), "America/Lima")


def ahora_lima() -> datetime:
    return datetime.now(ZONA_LIMA)


def hoy_lima() -> date:
    return ahora_lima().date()
