from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any

_POSITION_NUDGE = 1e-9


def import_rockphypy_gassmann_classes() -> tuple[Any, Any]:
    with _legacy_colormap_compat():
        from rockphypy import EM, Fluid  # type: ignore[import-not-found]

    return EM, Fluid


def import_rockphypy_granular_media_class() -> Any:
    with _legacy_colormap_compat():
        from rockphypy import GM  # type: ignore[import-not-found]

    return GM


def import_rockphypy_avo_class() -> Any:
    with _legacy_colormap_compat():
        from rockphypy import AVO  # type: ignore[import-not-found]

    return AVO


@contextmanager
def _legacy_colormap_compat():
    try:
        import matplotlib.colors as colors
    except Exception:
        yield
        return

    original_from_list = colors.LinearSegmentedColormap.from_list

    def compatible_from_list(name, color_values, N=256, gamma=1.0):
        try:
            return original_from_list(name, color_values, N=N, gamma=gamma)
        except ValueError as exc:
            adjusted = _nudge_duplicate_color_positions(color_values)
            if adjusted is None:
                raise exc
            return original_from_list(name, adjusted, N=N, gamma=gamma)

    colors.LinearSegmentedColormap.from_list = staticmethod(compatible_from_list)
    try:
        yield
    finally:
        colors.LinearSegmentedColormap.from_list = original_from_list


def _nudge_duplicate_color_positions(color_values: Any) -> list[tuple[float, Any]] | None:
    if not isinstance(color_values, Sequence):
        return None

    adjusted: list[tuple[float, Any]] = []
    previous_position = -1.0
    changed = False

    for item in color_values:
        if not _is_position_color_pair(item):
            return None

        position = float(item[0])
        if position <= previous_position:
            position = min(previous_position + _POSITION_NUDGE, 1.0)
            changed = True

        previous_position = position
        adjusted.append((position, item[1]))

    return adjusted if changed else None


def _is_position_color_pair(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) == 2
        and isinstance(value[0], (int, float))
    )
