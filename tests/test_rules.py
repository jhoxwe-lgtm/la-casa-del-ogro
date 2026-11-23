from datetime import datetime

import pytest

from casa_ogro.rules import (
    classify_occupancy,
    is_after_checkout_cutoff,
    is_confirmed_reservation,
    is_reading_stale,
)


def test_CP_RF15_02_conteo_menor_capacidad():
    assert classify_occupancy(19, 20) == "normal"


def test_CP_RF16_02_conteo_igual_capacidad():
    assert classify_occupancy(20, 20) == "completo"


def test_CP_RF16_03_conteo_superior_capacidad():
    assert classify_occupancy(21, 20) == "excedido"


@pytest.mark.parametrize(
    ("count", "capacity"),
    [(-1, 20), (True, 20), (10, 0)],
    ids=["conteo-negativo", "capacidad-cero"],
)
def test_CP_RF06_RF14_rechazar_valores_invalidos(count, capacity):
    with pytest.raises(ValueError):
        classify_occupancy(count, capacity)


def test_CP_RNF06_03_lectura_exactamente_dos_minutos_es_vigente():
    now = datetime.fromisoformat("2026-11-17T10:02:00-03:00")
    received = datetime.fromisoformat("2026-11-17T10:00:00-03:00")
    assert is_reading_stale(now, received) is False


def test_CP_RNF06_04_lectura_dos_minutos_y_un_segundo_es_antigua():
    now = datetime.fromisoformat("2026-11-17T10:02:01-03:00")
    received = datetime.fromisoformat("2026-11-17T10:00:00-03:00")
    assert is_reading_stale(now, received) is True


def test_CP_RF11_04_check_out_antes_del_mediodia():
    now = datetime.fromisoformat("2026-11-18T11:59:00-03:00")
    assert is_after_checkout_cutoff(now) is False


def test_CP_RF11_05_check_out_exactamente_al_mediodia():
    now = datetime.fromisoformat("2026-11-18T12:00:00-03:00")
    assert is_after_checkout_cutoff(now) is False


def test_CP_RF11_06_check_out_un_minuto_despues():
    now = datetime.fromisoformat("2026-11-18T12:01:00-03:00")
    assert is_after_checkout_cutoff(now) is True


def test_CP_RF12_05_reserva_confirmada_es_modificable():
    assert is_confirmed_reservation("confirmada") is True


@pytest.mark.parametrize(
    "status",
    ["en_curso", "completada", "cancelada"],
)
def test_CP_RF12_RF13_reservas_no_confirmadas_no_son_modificables(status):
    assert is_confirmed_reservation(status) is False
