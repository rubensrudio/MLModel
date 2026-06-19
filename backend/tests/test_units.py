from mlmodel.core.units import (
    fraction_to_percent,
    g_cm3_to_kg_m3,
    kg_m3_to_g_cm3,
    km_s_to_m_s,
    m_s_to_km_s,
    mpa_to_psi,
    percent_to_fraction,
    psi_to_mpa,
)


def test_porosity_unit_conversions() -> None:
    assert percent_to_fraction(20.0) == 0.2
    assert fraction_to_percent(0.245) == 24.5


def test_pressure_unit_conversions() -> None:
    assert round(psi_to_mpa(7500), 3) == 51.711
    assert round(mpa_to_psi(51.71067969876271), 1) == 7500.0


def test_density_unit_conversions() -> None:
    assert g_cm3_to_kg_m3(2.65) == 2650.0
    assert kg_m3_to_g_cm3(1000.0) == 1.0


def test_velocity_unit_conversions() -> None:
    assert km_s_to_m_s(4.5) == 4500.0
    assert m_s_to_km_s(6455.0) == 6.455
