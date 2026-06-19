PSI_TO_MPA = 0.006894757293168361


def percent_to_fraction(value: float) -> float:
    return value / 100.0


def fraction_to_percent(value: float) -> float:
    return value * 100.0


def psi_to_mpa(value: float) -> float:
    return value * PSI_TO_MPA


def mpa_to_psi(value: float) -> float:
    return value / PSI_TO_MPA


def g_cm3_to_kg_m3(value: float) -> float:
    return value * 1000.0


def kg_m3_to_g_cm3(value: float) -> float:
    return value / 1000.0


def km_s_to_m_s(value: float) -> float:
    return value * 1000.0


def m_s_to_km_s(value: float) -> float:
    return value / 1000.0
