"""
Solar System Sizing Service
===========================

Deterministically estimates a preliminary solar system size
from customer appliance usage or monthly electricity units.

The LLM may understand/extract the customer's words, but it
does NOT perform the final sizing mathematics.

Important:
    Results are preliminary sales estimates.

    Final engineering design should use actual appliance
    nameplate ratings, site conditions, solar irradiation,
    shading, orientation, inverter specifications and
    installation requirements.
"""

from math import ceil

from app.schemas.agent import ApplianceUsage, SolarSizingResult

# ============================================================
# CONFIGURABLE PRELIMINARY APPLIANCE ASSUMPTIONS
# ============================================================
#
# Customer-provided wattage always takes priority.
# These values are assumptions for preliminary sales sizing,
# not manufacturer specifications.
# ============================================================

DEFAULT_APPLIANCE_WATTS: dict[str, float] = {
    "fan": 75,
    "ceiling_fan": 75,
    "light": 12,
    "led_light": 12,
    "bulb": 12,
    "television": 100,
    "tv": 100,
    "refrigerator": 180,
    "fridge": 180,
    "computer": 200,
    "desktop": 200,
    "laptop": 65,
    "washing_machine": 500,
    "water_pump": 750,
    "iron": 1200,
    "microwave": 1200,
}

DEFAULT_DAILY_HOURS: dict[str, float] = {
    "fan": 8,
    "ceiling_fan": 8,
    "light": 6,
    "led_light": 6,
    "bulb": 6,
    "television": 4,
    "tv": 4,
    "refrigerator": 8,
    "fridge": 8,
    "computer": 6,
    "desktop": 6,
    "laptop": 6,
    "washing_machine": 1,
    "water_pump": 1,
    "iron": 0.5,
    "microwave": 0.5,
}

# Preliminary AC input-power assumptions.
AC_WATTS_BY_TON: dict[float, float] = {
    1.0: 1200,
    1.5: 1800,
    2.0: 2400,
}

# Configurable preliminary production assumptions.
DEFAULT_PEAK_SUN_HOURS = 5.0
SYSTEM_EFFICIENCY = 0.80
DESIGN_MARGIN = 1.15


def normalize_appliance_name(name: str) -> str:
    """Normalize an appliance name for catalog lookup."""

    return name.strip().lower().replace("-", "_").replace(" ", "_")


def get_ac_wattage(capacity_ton: float | None) -> float | None:
    """Estimate preliminary AC wattage from tonnage."""

    if capacity_ton is None:
        return None

    if capacity_ton in AC_WATTS_BY_TON:
        return AC_WATTS_BY_TON[capacity_ton]

    return capacity_ton * 1200


def resolve_appliance_wattage(
    appliance: ApplianceUsage,
) -> tuple[float | None, str | None]:
    """
    Resolve wattage in this priority:
        1. Customer-provided wattage
        2. AC tonnage estimate
        3. Configured appliance assumption
    """

    if appliance.wattage is not None:
        return float(appliance.wattage), None

    name = normalize_appliance_name(appliance.appliance)

    if name in {"ac", "air_conditioner", "airconditioner"}:
        ac_wattage = get_ac_wattage(appliance.capacity_ton)

        if ac_wattage is not None:
            return (
                ac_wattage,
                (
                    f"{appliance.capacity_ton:g}-ton AC estimated "
                    f"at {ac_wattage:,.0f} W for preliminary sizing."
                ),
            )

        return (
            None,
            "AC wattage/tonnage is required for accurate sizing.",
        )

    wattage = DEFAULT_APPLIANCE_WATTS.get(name)

    if wattage is None:
        return (
            None,
            (
                f"No configured preliminary wattage is available for "
                f"'{appliance.appliance}'."
            ),
        )

    return (
        wattage,
        (
            f"{appliance.appliance} estimated at "
            f"{wattage:,.0f} W each for preliminary sizing."
        ),
    )


def resolve_daily_hours(
    appliance: ApplianceUsage,
) -> tuple[float | None, str | None]:
    """Resolve daily operating hours."""

    if appliance.hours_per_day is not None:
        return float(appliance.hours_per_day), None

    name = normalize_appliance_name(appliance.appliance)

    hours = DEFAULT_DAILY_HOURS.get(name)

    if hours is None:
        if name in {"ac", "air_conditioner", "airconditioner"}:
            return None, "Daily AC usage hours are required."

        return (
            None,
            f"Daily usage hours are required for '{appliance.appliance}'.",
        )

    return (
        hours,
        (f"{appliance.appliance} assumed to operate {hours:g} hours/day."),
    )


def round_system_size(required_kw: float) -> float:
    """Round a system size upward to the next 0.5 kW."""

    return ceil(required_kw * 2) / 2


def estimate_from_monthly_units(
    monthly_units: float,
) -> SolarSizingResult:
    """
    Estimate preliminary solar size from monthly usage.

    One electricity unit is treated as one kWh.
    """

    if monthly_units <= 0:
        raise ValueError("Monthly electricity units must be greater than zero.")

    daily_energy = monthly_units / 30

    raw_system_kw = daily_energy / (DEFAULT_PEAK_SUN_HOURS * SYSTEM_EFFICIENCY)

    recommended_kw = round_system_size(raw_system_kw * DESIGN_MARGIN)

    return SolarSizingResult(
        estimated_peak_load_kw=0,
        estimated_daily_energy_kwh=round(daily_energy, 2),
        recommended_system_kw=recommended_kw,
        estimated_battery_kwh=None,
        assumptions=[
            (f"Monthly usage: {monthly_units:,.0f} kWh (electricity units)."),
            (
                f"Preliminary calculation uses "
                f"{DEFAULT_PEAK_SUN_HOURS:g} peak-sun-hours/day."
            ),
            (f"System efficiency assumption: {SYSTEM_EFFICIENCY * 100:.0f}%."),
            (f"Design margin: {(DESIGN_MARGIN - 1) * 100:.0f}%."),
        ],
    )


def estimate_from_appliances(
    appliances: list[ApplianceUsage],
    needs_backup: bool | None = None,
) -> SolarSizingResult | None:
    """Estimate preliminary solar size from appliance usage."""

    if not appliances:
        return None

    peak_load_watts = 0.0
    daily_energy_wh = 0.0
    assumptions: list[str] = []
    usable_appliance_count = 0

    for appliance in appliances:
        wattage, wattage_note = resolve_appliance_wattage(appliance)
        hours, hours_note = resolve_daily_hours(appliance)

        if wattage_note:
            assumptions.append(wattage_note)

        if hours_note:
            assumptions.append(hours_note)

        if wattage is None:
            continue

        quantity = appliance.quantity
        peak_load_watts += wattage * quantity

        if hours is not None:
            daily_energy_wh += wattage * quantity * hours
            usable_appliance_count += 1

    if usable_appliance_count == 0:
        return None

    peak_load_kw = peak_load_watts / 1000
    daily_energy_kwh = daily_energy_wh / 1000

    energy_based_kw = daily_energy_kwh / (DEFAULT_PEAK_SUN_HOURS * SYSTEM_EFFICIENCY)

    peak_based_kw = peak_load_kw

    raw_required_kw = max(
        energy_based_kw,
        peak_based_kw,
    )

    recommended_kw = round_system_size(raw_required_kw * DESIGN_MARGIN)

    estimated_battery_kwh = None

    if needs_backup is True:
        estimated_battery_kwh = round(
            daily_energy_kwh,
            2,
        )

        assumptions.append(
            "Battery estimate is preliminary; exact backup "
            "capacity depends on required backup appliances "
            "and backup duration."
        )

    assumptions.extend(
        [
            (
                f"Preliminary calculation uses "
                f"{DEFAULT_PEAK_SUN_HOURS:g} peak-sun-hours/day."
            ),
            (f"System efficiency assumption: {SYSTEM_EFFICIENCY * 100:.0f}%."),
            (f"Design margin: {(DESIGN_MARGIN - 1) * 100:.0f}%."),
        ]
    )

    return SolarSizingResult(
        estimated_peak_load_kw=round(peak_load_kw, 2),
        estimated_daily_energy_kwh=round(daily_energy_kwh, 2),
        recommended_system_kw=recommended_kw,
        estimated_battery_kwh=estimated_battery_kwh,
        assumptions=assumptions,
    )
