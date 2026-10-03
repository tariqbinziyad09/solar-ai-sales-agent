"""
Product API Schemas
===================

Pydantic schemas used by the Product Catalog API.

The catalog supports:
- Solar Panels
- Inverters
- Batteries
- Product updates
- Product activation/deactivation
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# CREATE SCHEMAS
# ============================================================


class SolarPanelCreate(BaseModel):
    """Create a solar panel."""

    name: str = Field(min_length=2, max_length=150)
    brand: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)

    wattage: int = Field(gt=0)
    technology: str | None = Field(default=None, max_length=100)
    efficiency: float | None = Field(default=None, gt=0, le=100)
    warranty_years: int | None = Field(default=None, ge=0)


class InverterCreate(BaseModel):
    """Create a solar inverter."""

    name: str = Field(min_length=2, max_length=150)
    brand: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)

    power_kw: float = Field(gt=0)
    inverter_type: str = Field(min_length=2, max_length=50)
    phase: str | None = Field(default=None, max_length=50)
    mppt_count: int | None = Field(default=None, gt=0)
    efficiency: float | None = Field(default=None, gt=0, le=100)
    warranty_years: int | None = Field(default=None, ge=0)


class BatteryCreate(BaseModel):
    """Create a solar battery."""

    name: str = Field(min_length=2, max_length=150)
    brand: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)

    chemistry: str | None = Field(default=None, max_length=50)
    capacity_kwh: float = Field(gt=0)
    voltage: float | None = Field(default=None, gt=0)
    cycle_life: int | None = Field(default=None, gt=0)
    warranty_years: int | None = Field(default=None, ge=0)


# ============================================================
# UPDATE SCHEMAS
# ============================================================


class ProductUpdate(BaseModel):
    """
    Update an existing product.

    All fields are optional because PATCH only changes
    fields supplied by the administrator.

    Category itself is intentionally not editable.
    A panel should not be converted into a battery/inverter.
    """

    # Common Product fields
    name: str | None = Field(default=None, min_length=2, max_length=150)
    brand: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)

    # Solar Panel fields
    wattage: int | None = Field(default=None, gt=0)
    technology: str | None = Field(default=None, max_length=100)

    # Shared Panel/Inverter field
    efficiency: float | None = Field(default=None, gt=0, le=100)

    # Shared technical field
    warranty_years: int | None = Field(default=None, ge=0)

    # Inverter fields
    power_kw: float | None = Field(default=None, gt=0)
    inverter_type: str | None = Field(default=None, min_length=2, max_length=50)
    phase: str | None = Field(default=None, max_length=50)
    mppt_count: int | None = Field(default=None, gt=0)

    # Battery fields
    chemistry: str | None = Field(default=None, max_length=50)
    capacity_kwh: float | None = Field(default=None, gt=0)
    voltage: float | None = Field(default=None, gt=0)
    cycle_life: int | None = Field(default=None, gt=0)


class ProductStatusUpdate(BaseModel):
    """Activate or deactivate a catalog product."""

    is_active: bool


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class SolarPanelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str | None
    sku: str | None
    description: str | None
    price: float | None
    is_active: bool
    created_at: datetime

    wattage: int
    technology: str | None
    efficiency: float | None
    warranty_years: int | None


class InverterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str | None
    sku: str | None
    description: str | None
    price: float | None
    is_active: bool
    created_at: datetime

    power_kw: float
    inverter_type: str
    phase: str | None
    mppt_count: int | None
    efficiency: float | None
    warranty_years: int | None


class BatteryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str | None
    sku: str | None
    description: str | None
    price: float | None
    is_active: bool
    created_at: datetime

    chemistry: str | None
    capacity_kwh: float
    voltage: float | None
    cycle_life: int | None
    warranty_years: int | None


class ProductResponse(BaseModel):
    """
    Unified catalog response.

    Only fields belonging to the product category
    will contain values.
    """

    id: int
    name: str
    brand: str | None
    category: str
    sku: str | None
    description: str | None
    price: float | None
    is_active: bool
    created_at: datetime

    # Panel
    wattage: int | None = None
    technology: str | None = None

    # Panel / Inverter
    efficiency: float | None = None

    # Inverter
    power_kw: float | None = None
    inverter_type: str | None = None
    phase: str | None = None
    mppt_count: int | None = None

    # Battery
    chemistry: str | None = None
    capacity_kwh: float | None = None
    voltage: float | None = None
    cycle_life: int | None = None

    # Shared technical field
    warranty_years: int | None = None
