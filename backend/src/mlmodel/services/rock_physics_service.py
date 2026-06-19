from math import sqrt

from mlmodel.schemas.rock_physics import GassmannRequest, GassmannResponse


class RockPhysicsService:
    def run_gassmann(self, request: GassmannRequest) -> GassmannResponse:
        result = _run_with_rockphypy(request)
        if result is None:
            result = _run_with_local_fallback(request)
        return result


def _run_with_rockphypy(request: GassmannRequest) -> GassmannResponse | None:
    try:
        from rockphypy import EM, Fluid  # type: ignore[import-not-found]
    except Exception:
        return None

    k_dry, g_dry = EM.cripor(
        request.mineral_bulk_modulus_gpa,
        request.mineral_shear_modulus_gpa,
        request.porosity_fraction,
        request.critical_porosity_fraction,
    )
    k_sat, g_sat = Fluid.Gassmann(
        k_dry,
        g_dry,
        request.mineral_bulk_modulus_gpa,
        request.fluid_bulk_modulus_gpa,
        request.porosity_fraction,
    )
    vp, vs, density = Fluid.vels(
        k_dry,
        g_dry,
        request.mineral_bulk_modulus_gpa,
        request.mineral_density_g_cm3,
        request.fluid_bulk_modulus_gpa,
        request.fluid_density_g_cm3,
        request.porosity_fraction,
    )
    return _response(
        k_dry=float(k_dry),
        g_dry=float(g_dry),
        k_sat=float(k_sat),
        g_sat=float(g_sat),
        density=float(density),
        vp_m_s=float(vp) * 1000,
        vs_m_s=float(vs) * 1000,
        engine="rockphypy",
    )


def _run_with_local_fallback(request: GassmannRequest) -> GassmannResponse:
    phi = request.porosity_fraction
    k0 = request.mineral_bulk_modulus_gpa
    g0 = request.mineral_shear_modulus_gpa
    kf = request.fluid_bulk_modulus_gpa

    k_dry = k0 * (1 - phi / request.critical_porosity_fraction)
    g_dry = g0 * (1 - phi / request.critical_porosity_fraction)
    k_sat = k_dry + ((1 - k_dry / k0) ** 2) / (
        phi / kf + (1 - phi) / k0 - k_dry / (k0**2)
    )
    g_sat = g_dry
    density = (1 - phi) * request.mineral_density_g_cm3 + phi * request.fluid_density_g_cm3
    vp_m_s = sqrt((k_sat + 4 * g_sat / 3) / density) * 1000
    vs_m_s = sqrt(g_sat / density) * 1000

    return _response(
        k_dry=k_dry,
        g_dry=g_dry,
        k_sat=k_sat,
        g_sat=g_sat,
        density=density,
        vp_m_s=vp_m_s,
        vs_m_s=vs_m_s,
        engine="local-gassmann-fallback",
    )


def _response(
    *,
    k_dry: float,
    g_dry: float,
    k_sat: float,
    g_sat: float,
    density: float,
    vp_m_s: float,
    vs_m_s: float,
    engine: str,
) -> GassmannResponse:
    return GassmannResponse(
        dry_bulk_modulus_gpa=k_dry,
        dry_shear_modulus_gpa=g_dry,
        saturated_bulk_modulus_gpa=k_sat,
        saturated_shear_modulus_gpa=g_sat,
        bulk_density_g_cm3=density,
        vp_m_s=vp_m_s,
        vs_m_s=vs_m_s,
        acoustic_impedance=vp_m_s * density,
        vp_vs_ratio=vp_m_s / vs_m_s,
        engine=engine,
        assumptions=[
            "Critical porosity model for dry frame",
            "Gassmann low-frequency fluid substitution",
            "Connected pore space and isotropic homogeneous rock",
            "Elastic moduli in GPa and density in g/cm3",
        ],
    )
