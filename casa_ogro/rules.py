"""Reglas puras del dominio, aisladas para pruebas unitarias."""


def classify_occupancy(count: int, capacity: int) -> str:
    """Clasifica un conteo válido frente a la capacidad configurada."""
    if count == capacity:
        return "completo"
    if count > capacity:
        return "excedido"
    return "normal"
