"""
Solar Package Schemas
=====================

Schemas used for creating, updating and returning
complete solar packages.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# PACKAGE ITEMS
# ============================================================


class PackageItemCreate(BaseModel):
    """One product included in a solar package."""

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class PackageItemResponse(BaseModel):
    """Basic package item response."""

    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int


# ============================================================
# CREATE PACKAGE
# ============================================================


class SolarPackageCreate(BaseModel):
    """Data required to create a complete solar package."""

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    system_size_kw: float = Field(gt=0)

    # hybrid / on-grid / off-grid
    system_type: str = Field(
        min_length=2,
        max_length=50,
    )

    package_price: float = Field(ge=0)

    # At least one product must exist.
    items: list[PackageItemCreate] = Field(
        min_length=1,
    )


# ============================================================
# UPDATE PACKAGE
# ============================================================


class SolarPackageUpdate(BaseModel):
    """
    Data used by the admin panel when editing a package.

    All fields are optional because PATCH is used.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    system_size_kw: float | None = Field(
        default=None,
        gt=0,
    )

    system_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    package_price: float | None = Field(
        default=None,
        ge=0,
    )

    items: list[PackageItemCreate] | None = None


class SolarPackageStatusUpdate(BaseModel):
    """Activate or deactivate a package."""

    is_active: bool


# ============================================================
# RESPONSES
# ============================================================


class SolarPackageResponse(BaseModel):
    """Basic complete package response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    system_size_kw: float
    system_type: str
    package_price: float
    is_active: bool
    created_at: datetime

    items: list[PackageItemResponse]


class PackageProductResponse(BaseModel):
    """
    Detailed product information shown inside
    the admin package manager.
    """

    product_id: int
    name: str
    brand: str | None
    category: str
    sku: str | None
    price: float | None
    is_active: bool
    quantity: int


class SolarPackageAdminResponse(BaseModel):
    """Detailed package returned to the admin frontend."""

    id: int
    name: str
    description: str | None
    system_size_kw: float
    system_type: str
    package_price: float
    is_active: bool
    created_at: datetime

    items: list[PackageProductResponse]
