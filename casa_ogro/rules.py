"""Reglas de negocio puras para facilitar pruebas unitarias de caja blanca."""

from datetime import datetime, timedelta


def classify_occupancy(count: int, capacity: int) -> str:
    """Clasifica un aforo en normal, completo o excedido."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("El conteo debe ser un entero igual o mayor que cero.")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("La capacidad debe ser un entero mayor que cero.")
    if count < capacity:
        return "normal"
    if count == capacity:
        return "completo"
    return "excedido"


def is_reading_stale(now: datetime, received_at: datetime, max_age_minutes: int = 2) -> bool:
    """Indica si una lectura superó la antigüedad máxima permitida."""
    return now - received_at > timedelta(minutes=max_age_minutes)


def is_after_checkout_cutoff(now: datetime) -> bool:
    """Recepción necesita autorización después de las 12:00:00."""
    return (now.hour, now.minute, now.second, now.microsecond) > (12, 0, 0, 0)


def is_confirmed_reservation(status: str) -> bool:
    """Solo las reservas confirmadas admiten modificación o cancelación."""
    return status == "confirmada"
