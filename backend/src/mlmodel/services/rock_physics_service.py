from math import cos, pi, sin, sqrt, tan
from typing import Any

from mlmodel.integrations.rockphypy_compat import (
    import_rockphypy_avo_class,
    import_rockphypy_gassmann_classes,
    import_rockphypy_granular_media_class,
)
from mlmodel.schemas.rock_physics import (
    AkiRichardsRequest,
    AkiRichardsResponse,
    GassmannRequest,
    GassmannResponse,
    GranularMediaRequest,
    GranularMediaResponse,
)


class RockPhysicsService:
    def run_gassmann(self, request: GassmannRequest) -> GassmannResponse:
        result = _run_with_rockphypy(request)
        if result is None:
            result = _run_with_local_fallback(request)
        return result

    def run_softsand(self, request: GranularMediaRequest) -> GranularMediaResponse:
        result = _run_granular_media_with_rockphypy(request, model="softsand")
        if result is None:
            result = _run_granular_media_with_local_fallback(request, model="softsand")
        return result

    def run_stiffsand(self, request: GranularMediaRequest) -> GranularMediaResponse:
        result = _run_granular_media_with_rockphypy(request, model="stiffsand")
        if result is None:
            result = _run_granular_media_with_local_fallback(request, model="stiffsand")
        return result

    def run_aki_richards(self, request: AkiRichardsRequest) -> AkiRichardsResponse:
        result = _run_aki_richards_with_rockphypy(request)
        if result is None:
            result = _run_aki_richards_with_local_fallback(request)
        return result


def _run_with_rockphypy(request: GassmannRequest) -> GassmannResponse | None:
    try:
        EM, Fluid = import_rockphypy_gassmann_classes()
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
        vp_m_s=float(vp),
        vs_m_s=float(vs),
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


def _run_granular_media_with_rockphypy(
    request: GranularMediaRequest,
    *,
    model: str,
) -> GranularMediaResponse | None:
    try:
        GM = import_rockphypy_granular_media_class()
        model_function = getattr(GM, model)
    except Exception:
        return None

    k_dry, g_dry = model_function(
        request.mineral_bulk_modulus_gpa,
        request.mineral_shear_modulus_gpa,
        request.porosity_fraction,
        request.critical_porosity_fraction,
        request.coordination_number,
        request.effective_stress_mpa,
        request.reduced_shear_factor,
    )
    return _granular_media_response(
        k_dry=float(k_dry),
        g_dry=float(g_dry),
        engine="rockphypy",
        model=model,
    )


def _run_granular_media_with_local_fallback(
    request: GranularMediaRequest,
    *,
    model: str,
) -> GranularMediaResponse:
    k_hm, g_hm = _hertz_mindlin(
        request.mineral_bulk_modulus_gpa,
        request.mineral_shear_modulus_gpa,
        request.critical_porosity_fraction,
        request.coordination_number,
        request.effective_stress_mpa,
        request.reduced_shear_factor,
    )
    phi_ratio = request.porosity_fraction / request.critical_porosity_fraction

    if model == "softsand":
        k_ref = k_hm
        g_ref = g_hm
    else:
        k_ref = request.mineral_bulk_modulus_gpa
        g_ref = request.mineral_shear_modulus_gpa

    k_dry = -4 / 3 * g_ref + (
        (phi_ratio / (k_hm + 4 / 3 * g_ref))
        + ((1 - phi_ratio) / (request.mineral_bulk_modulus_gpa + 4 / 3 * g_ref))
    ) ** -1
    auxiliary = g_ref / 6 * (
        (9 * k_ref + 8 * g_ref)
        / (k_ref + 2 * g_ref)
    )
    g_dry = -auxiliary + (
        (phi_ratio / (g_hm + auxiliary))
        + ((1 - phi_ratio) / (request.mineral_shear_modulus_gpa + auxiliary))
    ) ** -1

    return _granular_media_response(
        k_dry=k_dry,
        g_dry=g_dry,
        engine="local-granular-media-fallback",
        model=model,
    )


def _hertz_mindlin(
    mineral_bulk_modulus_gpa: float,
    mineral_shear_modulus_gpa: float,
    critical_porosity_fraction: float,
    coordination_number: float,
    effective_stress_mpa: float,
    reduced_shear_factor: float,
) -> tuple[float, float]:
    effective_stress_gpa = effective_stress_mpa / 1000
    poisson_ratio = (3 * mineral_bulk_modulus_gpa - 2 * mineral_shear_modulus_gpa) / (
        6 * mineral_bulk_modulus_gpa + 2 * mineral_shear_modulus_gpa
    )
    k_hm = (
        effective_stress_gpa
        * (
            coordination_number**2
            * (1 - critical_porosity_fraction) ** 2
            * mineral_shear_modulus_gpa**2
        )
        / (18 * pi**2 * (1 - poisson_ratio) ** 2)
    ) ** (1 / 3)
    g_hm = (
        (2 + 3 * reduced_shear_factor - poisson_ratio * (1 + 3 * reduced_shear_factor))
        / (5 * (2 - poisson_ratio))
    ) * (
        effective_stress_gpa
        * (
            3
            * coordination_number**2
            * (1 - critical_porosity_fraction) ** 2
            * mineral_shear_modulus_gpa**2
        )
        / (2 * pi**2 * (1 - poisson_ratio) ** 2)
    ) ** (1 / 3)
    return k_hm, g_hm


def _run_aki_richards_with_rockphypy(request: AkiRichardsRequest) -> AkiRichardsResponse | None:
    try:
        AVO = import_rockphypy_avo_class()
    except Exception:
        return None

    pp_reflectivity, ps_reflectivity, intercept, gradient = AVO.Aki_Richards(
        request.incident_angles_degrees,
        request.vp_upper_m_s,
        request.vp_lower_m_s,
        request.vs_upper_m_s,
        request.vs_lower_m_s,
        request.density_upper_kg_m3,
        request.density_lower_kg_m3,
    )
    return _aki_richards_response(
        pp_reflectivity=_to_float_list(pp_reflectivity),
        ps_reflectivity=_to_float_list(ps_reflectivity),
        intercept=float(intercept),
        gradient=float(gradient),
        engine="rockphypy",
    )


def _run_aki_richards_with_local_fallback(request: AkiRichardsRequest) -> AkiRichardsResponse:
    delta_density = request.density_lower_kg_m3 - request.density_upper_kg_m3
    delta_vp = request.vp_lower_m_s - request.vp_upper_m_s
    delta_vs = request.vs_lower_m_s - request.vs_upper_m_s
    mean_density = 0.5 * (request.density_upper_kg_m3 + request.density_lower_kg_m3)
    mean_vp = 0.5 * (request.vp_upper_m_s + request.vp_lower_m_s)
    mean_vs = 0.5 * (request.vs_upper_m_s + request.vs_lower_m_s)

    intercept = 0.5 * (delta_density / mean_density + delta_vp / mean_vp)
    m_term = -2 * (mean_vs / mean_vp) ** 2 * (
        2 * delta_vs / mean_vs + delta_density / mean_density
    )
    n_term = 0.5 * delta_vp / mean_vp
    gradient = m_term + n_term

    pp_reflectivity = []
    ps_reflectivity = []
    for angle_degrees in request.incident_angles_degrees:
        angle = angle_degrees * pi / 180
        ray_parameter = sin(angle) / request.vp_upper_m_s
        converted_cosine = sqrt(
            1 - (sin(angle) ** 2 * (request.vs_upper_m_s**2 / request.vp_upper_m_s**2))
        )
        pp_reflectivity.append(intercept + m_term * sin(angle) ** 2 + n_term * tan(angle) ** 2)
        ps_reflectivity.append(
            -0.5
            * ray_parameter
            * mean_vp
            / converted_cosine
            * (
                (
                    1
                    - 2 * mean_vs**2 * ray_parameter**2
                    + 2 * mean_vs**2 * cos(angle) / mean_vp * converted_cosine / mean_vs
                )
                * delta_density
                / mean_density
                - (
                    4 * ray_parameter**2 * mean_vs**2
                    - 4 * mean_vs**2 * cos(angle) / mean_vp * converted_cosine / mean_vs
                )
                * delta_vs
                / mean_vs
            )
        )

    return _aki_richards_response(
        pp_reflectivity=pp_reflectivity,
        ps_reflectivity=ps_reflectivity,
        intercept=intercept,
        gradient=gradient,
        engine="local-avo-fallback",
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


def _granular_media_response(
    *,
    k_dry: float,
    g_dry: float,
    engine: str,
    model: str,
) -> GranularMediaResponse:
    model_label = "Soft-sand" if model == "softsand" else "Stiff-sand"
    return GranularMediaResponse(
        dry_bulk_modulus_gpa=k_dry,
        dry_shear_modulus_gpa=g_dry,
        engine=engine,
        assumptions=[
            f"{model_label} dry-frame model",
            "Hertz-Mindlin critical porosity endpoint",
            "Elastic moduli in GPa",
            "Effective stress in MPa",
        ],
    )


def _aki_richards_response(
    *,
    pp_reflectivity: list[float],
    ps_reflectivity: list[float],
    intercept: float,
    gradient: float,
    engine: str,
) -> AkiRichardsResponse:
    return AkiRichardsResponse(
        pp_reflectivity=pp_reflectivity,
        ps_reflectivity=ps_reflectivity,
        intercept=intercept,
        gradient=gradient,
        engine=engine,
        assumptions=[
            "Aki-Richards PP reflectivity approximation",
            "Incident angles in degrees",
            "Velocities in m/s",
            "Densities in kg/m3",
        ],
    )


def _to_float_list(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, tuple):
        return [float(item) for item in value]
    return [float(value)]
