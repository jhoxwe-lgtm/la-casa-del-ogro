"""Pruebas unitarias de caja blanca: dos decisiones, V(G)=3."""
from casa_ogro.rules import classify_occupancy


def test_unit_CP_RF15_01_conteo_inferior_a_capacidad_es_normal():
    assert classify_occupancy(19, 20) == "normal"


def test_unit_CP_RF16_01_conteo_igual_a_capacidad_es_completo():
    assert classify_occupancy(20, 20) == "completo"


def test_unit_CP_RF16_02_conteo_superior_a_capacidad_es_excedido():
    assert classify_occupancy(21, 20) == "excedido"
