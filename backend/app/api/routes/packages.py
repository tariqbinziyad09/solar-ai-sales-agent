"""
Solar Package API Routes
========================
Public/recommendation package APIs and
admin package management APIs.
"""

from typing import Annotated

from app.database.database import get_db
from app.models.battery import Battery
from app.models.inverter import Inverter
from app.models.solar_panel import SolarPanel
from app.schemas.package import (
    SolarPackageAdminResponse,
    SolarPackageCreate,
    SolarPackageResponse,
    SolarPackageStatusUpdate,
    SolarPackageUpdate,
)
from app.services.package_service import (
    create_solar_package,
    get_admin_packages,
    get_package_by_id,
    get_packages,
    set_package_status,
    update_solar_package,
)
from app.services.rbac_service import require_admin, require_staff
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/packages",
    tags=["Solar Packages"],
)


# ============================================================
# RESPONSE HELPER
# ============================================================
def serialize_admin_package(package):
    """
    Convert SQLAlchemy package into frontend-friendly
    admin response.
    """
    items = []
    for item in package.items:
        product = item.product
        items.append(
            {
                "product_id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "sku": product.sku,
                "price": product.price,
                "is_active": product.is_active,
                "quantity": item.quantity,
            }
        )
    return {
        "id": package.id,
        "name": package.name,
        "description": package.description,
        "system_size_kw": package.system_size_kw,
        "system_type": package.system_type,
        "package_price": package.package_price,
        "is_active": package.is_active,
        "created_at": package.created_at,
        "items": items,
    }


# ============================================================
# ADMIN - ALL PACKAGES
# ============================================================
@router.get(
    "/admin/all",
    response_model=list[SolarPackageAdminResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_admin_packages(
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_staff),
):
    """
    Return all packages including inactive packages.
    Used by the admin dashboard.
    """
    packages = get_admin_packages(db)
    return [serialize_admin_package(package) for package in packages]


# ============================================================
# ACTIVE PACKAGES / RECOMMENDATION ENGINE
# ============================================================
@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
def get_all_packages(
    db: Annotated[Session, Depends(get_db)],
    system_type: str | None = None,
    min_size_kw: float | None = None,
    max_size_kw: float | None = None,
    max_price: float | None = None,
):
    """
    Return ACTIVE solar packages with optional filters.
    Example:
    /api/packages?system_type=hybrid&max_price=1400000
    """
    return get_packages(
        db=db,
        system_type=system_type,
        min_size_kw=min_size_kw,
        max_size_kw=max_size_kw,
        max_price=max_price,
    )


# ============================================================
# CREATE PACKAGE
# ============================================================
@router.post(
    "",
    response_model=SolarPackageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_package(
    package_data: SolarPackageCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Create a complete solar package."""
    try:
        return create_solar_package(
            db=db,
            package_data=package_data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create solar package.",
        ) from error


# ============================================================
# GET ONE PACKAGE
# ============================================================
@router.get(
    "/{package_id}",
    status_code=status.HTTP_200_OK,
)
def get_package(
    package_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Return complete package with detailed
    product specifications.
    """
    package = get_package_by_id(
        db=db,
        package_id=package_id,
    )
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solar package not found.",
        )
    items = []
    for item in package.items:
        product = item.product
        product_data = {
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "sku": product.sku,
            "price": product.price,
            "is_active": product.is_active,
            "quantity": item.quantity,
            "specifications": {},
        }
        # --------------------------------------------
        # PANEL
        # --------------------------------------------
        if product.category == "panel":
            panel = (
                db.query(SolarPanel).filter(SolarPanel.product_id == product.id).first()
            )
            if panel:
                product_data["specifications"] = {
                    "wattage": panel.wattage,
                    "technology": panel.technology,
                    "efficiency": panel.efficiency,
                    "warranty_years": panel.warranty_years,
                }
        # --------------------------------------------
        # INVERTER
        # --------------------------------------------
        elif product.category == "inverter":
            inverter = (
                db.query(Inverter).filter(Inverter.product_id == product.id).first()
            )
            if inverter:
                product_data["specifications"] = {
                    "power_kw": inverter.power_kw,
                    "inverter_type": inverter.inverter_type,
                    "phase": inverter.phase,
                    "mppt_count": inverter.mppt_count,
                    "efficiency": inverter.efficiency,
                    "warranty_years": inverter.warranty_years,
                }
        # --------------------------------------------
        # BATTERY
        # --------------------------------------------
        elif product.category == "battery":
            battery = db.query(Battery).filter(Battery.product_id == product.id).first()
            if battery:
                product_data["specifications"] = {
                    "chemistry": battery.chemistry,
                    "capacity_kwh": battery.capacity_kwh,
                    "voltage": battery.voltage,
                    "cycle_life": battery.cycle_life,
                    "warranty_years": battery.warranty_years,
                }
        items.append(product_data)
    return {
        "id": package.id,
        "name": package.name,
        "description": package.description,
        "system_size_kw": package.system_size_kw,
        "system_type": package.system_type,
        "package_price": package.package_price,
        "is_active": package.is_active,
        "created_at": package.created_at,
        "items": items,
    }


# ============================================================
# UPDATE PACKAGE
# ============================================================
@router.patch(
    "/{package_id}",
    response_model=SolarPackageAdminResponse,
    status_code=status.HTTP_200_OK,
)
def update_package(
    package_id: int,
    package_data: SolarPackageUpdate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Edit package details and package products."""
    package = get_package_by_id(
        db=db,
        package_id=package_id,
    )
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solar package not found.",
        )
    try:
        package = update_solar_package(
            db=db,
            package=package,
            package_data=package_data,
        )
        return serialize_admin_package(package)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update solar package.",
        ) from error


# ============================================================
# ACTIVATE / DEACTIVATE
# ============================================================
@router.patch(
    "/{package_id}/status",
    response_model=SolarPackageAdminResponse,
    status_code=status.HTTP_200_OK,
)
def update_package_status(
    package_id: int,
    status_data: SolarPackageStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),  # noqa: B008
):
    """Activate or deactivate a solar package."""
    package = get_package_by_id(
        db=db,
        package_id=package_id,
    )
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solar package not found.",
        )
    try:
        package = set_package_status(
            db=db,
            package=package,
            is_active=status_data.is_active,
        )
        # Reload relationships before serialization.
        package = get_package_by_id(
            db=db,
            package_id=package.id,
        )
        return serialize_admin_package(package)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change package status.",
        ) from error
