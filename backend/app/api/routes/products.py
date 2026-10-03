"""
Product API Routes
==================

Internal CRM product catalog endpoints.

Permissions:
- Admin: read + create + update + activate/deactivate
- Sales Manager: read only
- Sales Executive: read only

Public AI/recommendation services can continue using the service layer directly.
"""

from typing import Annotated, Literal

from app.database.database import get_db
from app.schemas.product import (
    BatteryCreate,
    InverterCreate,
    ProductResponse,
    ProductStatusUpdate,
    ProductUpdate,
    SolarPanelCreate,
)
from app.services.product_service import (
    create_battery,
    create_inverter,
    create_solar_panel,
    get_all_products,
    get_product_by_id,
    serialize_product,
    set_product_status,
    update_product,
)
from app.services.rbac_service import require_admin, require_staff
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_staff),
    category: Literal["panel", "inverter", "battery"] | None = Query(default=None),
    active_only: bool = Query(default=False),
):
    """Return catalog products to authenticated CRM staff."""
    products = get_all_products(
        db=db,
        category=category,
        active_only=active_only,
    )
    return [serialize_product(db=db, product=product) for product in products]


@router.post(
    "/batteries",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_battery(
    battery_data: BatteryCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Admin-only battery creation."""
    try:
        product, _ = create_battery(db=db, battery_data=battery_data)
        return serialize_product(db=db, product=product)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create battery.",
        ) from error


@router.post(
    "/inverters",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_inverter(
    inverter_data: InverterCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Admin-only inverter creation."""
    try:
        product, _ = create_inverter(db=db, inverter_data=inverter_data)
        return serialize_product(db=db, product=product)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create inverter.",
        ) from error


@router.post(
    "/panels",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_panel(
    panel_data: SolarPanelCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Admin-only solar-panel creation."""
    try:
        product, _ = create_solar_panel(db=db, panel_data=panel_data)
        return serialize_product(db=db, product=product)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create solar panel.",
        ) from error


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_staff),
):
    """Return one product to authenticated CRM staff."""
    product = get_product_by_id(db=db, product_id=product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return serialize_product(db=db, product=product)


@router.patch("/{product_id}", response_model=ProductResponse)
def edit_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Admin-only product update."""
    product = get_product_by_id(db=db, product_id=product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    try:
        product = update_product(
            db=db,
            product=product,
            product_data=product_data,
        )
        return serialize_product(db=db, product=product)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update product.",
        ) from error


@router.patch("/{product_id}/status", response_model=ProductResponse)
def change_product_status(
    product_id: int,
    status_data: ProductStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    _current_user=Depends(require_admin),
):
    """Admin-only product activation/deactivation."""
    product = get_product_by_id(db=db, product_id=product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    try:
        product = set_product_status(
            db=db,
            product=product,
            is_active=status_data.is_active,
        )
        return serialize_product(db=db, product=product)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change product status.",
        ) from error
