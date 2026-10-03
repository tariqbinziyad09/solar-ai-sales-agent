"""
Solar Package Service
=====================

Business logic for creating, retrieving,
filtering and administrating solar packages.
"""

from app.models.package_item import PackageItem
from app.models.product import Product
from app.models.solar_package import SolarPackage
from app.schemas.package import (
    SolarPackageCreate,
    SolarPackageUpdate,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

# ============================================================
# VALIDATE PACKAGE ITEMS
# ============================================================


def validate_package_items(
    db: Session,
    items,
) -> None:
    """
    Validate products before they are attached to a package.

    Rules:
    - Package must contain at least one product.
    - Every product must exist.
    - Duplicate products are not allowed.
    """

    if not items:
        raise ValueError("A solar package must contain at least one product.")

    product_ids = [item.product_id for item in items]

    # Prevent duplicate products.
    if len(product_ids) != len(set(product_ids)):
        raise ValueError("The same product cannot be added twice.")

    existing_products = db.query(Product).filter(Product.id.in_(product_ids)).all()

    existing_ids = {product.id for product in existing_products}

    missing_ids = set(product_ids) - existing_ids

    if missing_ids:
        raise ValueError(f"Products not found: {sorted(missing_ids)}")


# ============================================================
# CREATE PACKAGE
# ============================================================


def create_solar_package(
    db: Session,
    package_data: SolarPackageCreate,
) -> SolarPackage:
    """
    Create a complete solar package.

    Flow:
        Validate Products
              ↓
        Create Package
              ↓
          db.flush()
              ↓
        Create Items
              ↓
          db.commit()
    """

    try:
        validate_package_items(
            db=db,
            items=package_data.items,
        )

        solar_package = SolarPackage(
            name=package_data.name,
            description=package_data.description,
            system_size_kw=package_data.system_size_kw,
            system_type=package_data.system_type,
            package_price=package_data.package_price,
        )

        db.add(solar_package)

        # Generate package ID before commit.
        db.flush()

        for item in package_data.items:
            package_item = PackageItem(
                package_id=solar_package.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )

            db.add(package_item)

        db.commit()
        db.refresh(solar_package)

        return solar_package

    except (SQLAlchemyError, ValueError):
        db.rollback()
        raise


# ============================================================
# GET ONE PACKAGE
# ============================================================


def get_package_by_id(
    db: Session,
    package_id: int,
) -> SolarPackage | None:
    """
    Return one package including package items
    and their products.
    """

    return (
        db.query(SolarPackage)
        .options(selectinload(SolarPackage.items).selectinload(PackageItem.product))
        .filter(SolarPackage.id == package_id)
        .first()
    )


# ============================================================
# RECOMMENDATION ENGINE PACKAGE LIST
# ============================================================


def get_packages(
    db: Session,
    system_type: str | None = None,
    min_size_kw: float | None = None,
    max_size_kw: float | None = None,
    max_price: float | None = None,
) -> list[SolarPackage]:
    """
    Return ACTIVE packages for the recommendation engine.

    IMPORTANT:
    This function intentionally continues to hide
    inactive packages.
    """

    # SQL Server BIT:
    # 1 = True
    # 0 = False
    query = db.query(SolarPackage).filter(SolarPackage.is_active == 1)

    if system_type:
        query = query.filter(SolarPackage.system_type == system_type)

    if min_size_kw is not None:
        query = query.filter(SolarPackage.system_size_kw >= min_size_kw)

    if max_size_kw is not None:
        query = query.filter(SolarPackage.system_size_kw <= max_size_kw)

    if max_price is not None:
        query = query.filter(SolarPackage.package_price <= max_price)

    return query.order_by(SolarPackage.package_price.asc()).all()


# ============================================================
# ADMIN PACKAGE LIST
# ============================================================


def get_admin_packages(
    db: Session,
) -> list[SolarPackage]:
    """
    Return ALL packages for the admin dashboard.

    Unlike get_packages(), this includes inactive packages.
    """

    return (
        db.query(SolarPackage)
        .options(selectinload(SolarPackage.items).selectinload(PackageItem.product))
        .order_by(SolarPackage.id.desc())
        .all()
    )


# ============================================================
# UPDATE PACKAGE
# ============================================================


def update_solar_package(
    db: Session,
    package: SolarPackage,
    package_data: SolarPackageUpdate,
) -> SolarPackage:
    """
    Update package information and optionally
    replace its package items.
    """

    try:
        update_data = package_data.model_dump(exclude_unset=True)

        # Items require separate handling.
        items = update_data.pop(
            "items",
            None,
        )

        # --------------------------------------------
        # Update normal package fields
        # --------------------------------------------

        for field, value in update_data.items():
            # Prevent required DB fields from
            # accidentally becoming NULL.
            if (
                field
                in {
                    "name",
                    "system_size_kw",
                    "system_type",
                    "package_price",
                }
                and value is None
            ):
                raise ValueError(f"{field} cannot be null.")

            setattr(
                package,
                field,
                value,
            )

        # --------------------------------------------
        # Replace package products if supplied
        # --------------------------------------------

        if items is not None:
            validate_package_items(
                db=db,
                items=items,
            )

            # Delete current package composition.
            (
                db.query(PackageItem)
                .filter(PackageItem.package_id == package.id)
                .delete(synchronize_session=False)
            )

            # Insert new composition.
            for item in items:
                db.add(
                    PackageItem(
                        package_id=package.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                    )
                )

        db.commit()

        # Reload package + relationships.
        updated_package = get_package_by_id(
            db=db,
            package_id=package.id,
        )

        return updated_package

    except (SQLAlchemyError, ValueError):
        db.rollback()
        raise


# ============================================================
# ACTIVATE / DEACTIVATE
# ============================================================


def set_package_status(
    db: Session,
    package: SolarPackage,
    is_active: bool,
) -> SolarPackage:
    """
    Activate or deactivate a package.

    We intentionally avoid hard deletion because
    historical proposals may reference the package.
    """

    try:
        package.is_active = is_active

        db.commit()
        db.refresh(package)

        return package

    except SQLAlchemyError:
        db.rollback()
        raise
