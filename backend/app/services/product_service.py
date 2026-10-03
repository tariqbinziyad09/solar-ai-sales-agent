"""
Product Service
===============

Business logic for the Solar Product Catalog.

Responsibilities:
- Create products
- List products
- Fetch product details
- Update products
- Activate/deactivate products

Specialized products are stored across:

    products
       +
    solar_panels / inverters / batteries
"""

from app.models.battery import Battery
from app.models.inverter import Inverter
from app.models.product import Product
from app.models.solar_panel import SolarPanel
from app.schemas.product import (
    BatteryCreate,
    InverterCreate,
    ProductUpdate,
    SolarPanelCreate,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# ============================================================
# CREATE BATTERY
# ============================================================


def create_battery(
    db: Session,
    battery_data: BatteryCreate,
) -> tuple[Product, Battery]:

    try:
        product = Product(
            name=battery_data.name,
            brand=battery_data.brand,
            category="battery",
            sku=battery_data.sku,
            description=battery_data.description,
            price=battery_data.price,
        )

        db.add(product)
        db.flush()

        battery = Battery(
            product_id=product.id,
            chemistry=battery_data.chemistry,
            capacity_kwh=battery_data.capacity_kwh,
            voltage=battery_data.voltage,
            cycle_life=battery_data.cycle_life,
            warranty_years=battery_data.warranty_years,
        )

        db.add(battery)

        db.commit()

        db.refresh(product)
        db.refresh(battery)

        return product, battery

    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# CREATE INVERTER
# ============================================================


def create_inverter(
    db: Session,
    inverter_data: InverterCreate,
) -> tuple[Product, Inverter]:

    try:
        product = Product(
            name=inverter_data.name,
            brand=inverter_data.brand,
            category="inverter",
            sku=inverter_data.sku,
            description=inverter_data.description,
            price=inverter_data.price,
        )

        db.add(product)
        db.flush()

        inverter = Inverter(
            product_id=product.id,
            power_kw=inverter_data.power_kw,
            inverter_type=inverter_data.inverter_type,
            phase=inverter_data.phase,
            mppt_count=inverter_data.mppt_count,
            efficiency=inverter_data.efficiency,
            warranty_years=inverter_data.warranty_years,
        )

        db.add(inverter)

        db.commit()

        db.refresh(product)
        db.refresh(inverter)

        return product, inverter

    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# CREATE SOLAR PANEL
# ============================================================


def create_solar_panel(
    db: Session,
    panel_data: SolarPanelCreate,
) -> tuple[Product, SolarPanel]:

    try:
        product = Product(
            name=panel_data.name,
            brand=panel_data.brand,
            category="panel",
            sku=panel_data.sku,
            description=panel_data.description,
            price=panel_data.price,
        )

        db.add(product)
        db.flush()

        panel = SolarPanel(
            product_id=product.id,
            wattage=panel_data.wattage,
            technology=panel_data.technology,
            efficiency=panel_data.efficiency,
            warranty_years=panel_data.warranty_years,
        )

        db.add(panel)

        db.commit()

        db.refresh(product)
        db.refresh(panel)

        return product, panel

    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# GET SPECIALIZED RECORD
# ============================================================


def get_specialized_product(
    db: Session,
    product: Product,
):
    """
    Return the specialized record belonging to a product.
    """

    if product.category == "panel":
        return db.scalar(select(SolarPanel).where(SolarPanel.product_id == product.id))

    if product.category == "inverter":
        return db.scalar(select(Inverter).where(Inverter.product_id == product.id))

    if product.category == "battery":
        return db.scalar(select(Battery).where(Battery.product_id == product.id))

    return None


# ============================================================
# SERIALIZE PRODUCT
# ============================================================


def serialize_product(
    db: Session,
    product: Product,
) -> dict:
    """
    Combine the base Product row and its specialized
    technical specifications into one API response.
    """

    data = {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "sku": product.sku,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "created_at": product.created_at,
        "wattage": None,
        "technology": None,
        "efficiency": None,
        "warranty_years": None,
        "power_kw": None,
        "inverter_type": None,
        "phase": None,
        "mppt_count": None,
        "chemistry": None,
        "capacity_kwh": None,
        "voltage": None,
        "cycle_life": None,
    }

    specialized = get_specialized_product(
        db=db,
        product=product,
    )

    if specialized is None:
        return data

    if product.category == "panel":
        data.update(
            {
                "wattage": specialized.wattage,
                "technology": specialized.technology,
                "efficiency": specialized.efficiency,
                "warranty_years": specialized.warranty_years,
            }
        )

    elif product.category == "inverter":
        data.update(
            {
                "power_kw": specialized.power_kw,
                "inverter_type": specialized.inverter_type,
                "phase": specialized.phase,
                "mppt_count": specialized.mppt_count,
                "efficiency": specialized.efficiency,
                "warranty_years": specialized.warranty_years,
            }
        )

    elif product.category == "battery":
        data.update(
            {
                "chemistry": specialized.chemistry,
                "capacity_kwh": specialized.capacity_kwh,
                "voltage": specialized.voltage,
                "cycle_life": specialized.cycle_life,
                "warranty_years": specialized.warranty_years,
            }
        )

    return data


# ============================================================
# GET ALL PRODUCTS
# ============================================================


def get_all_products(
    db: Session,
    category: str | None = None,
    active_only: bool = False,
) -> list[Product]:
    """
    Return catalog products.

    Optional filters:
    - category
    - active_only
    """

    statement = select(Product)

    if category:
        statement = statement.where(Product.category == category)

    if active_only:
        # SQL Server BIT columns require "= 1".
        # Using .is_(True) generates "IS 1",
        # which SQL Server does not accept.
        statement = statement.where(Product.is_active == True)

    statement = statement.order_by(Product.id.desc())

    return list(db.scalars(statement).all())


# ============================================================
# GET PRODUCT
# ============================================================


def get_product_by_id(
    db: Session,
    product_id: int,
) -> Product | None:

    return db.get(
        Product,
        product_id,
    )


# ============================================================
# UPDATE PRODUCT
# ============================================================


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:
    """
    Update common and category-specific product data.

    Only fields explicitly supplied in the PATCH request
    are modified.
    """

    try:
        updates = product_data.model_dump(exclude_unset=True)

        # ----------------------------------------------------
        # COMMON PRODUCT FIELDS
        # ----------------------------------------------------

        common_fields = {
            "name",
            "brand",
            "sku",
            "description",
            "price",
        }

        for field in common_fields:
            if field in updates:
                setattr(
                    product,
                    field,
                    updates[field],
                )

        # ----------------------------------------------------
        # SPECIALIZED PRODUCT
        # ----------------------------------------------------

        specialized = get_specialized_product(
            db=db,
            product=product,
        )

        if specialized is None:
            raise ValueError(
                f"Technical specifications for product {product.id} were not found."
            )

        if product.category == "panel":
            allowed_fields = {
                "wattage",
                "technology",
                "efficiency",
                "warranty_years",
            }

        elif product.category == "inverter":
            allowed_fields = {
                "power_kw",
                "inverter_type",
                "phase",
                "mppt_count",
                "efficiency",
                "warranty_years",
            }

        elif product.category == "battery":
            allowed_fields = {
                "chemistry",
                "capacity_kwh",
                "voltage",
                "cycle_life",
                "warranty_years",
            }

        else:
            raise ValueError(f"Unsupported product category: {product.category}")

        for field in allowed_fields:
            if field in updates:
                setattr(
                    specialized,
                    field,
                    updates[field],
                )

        db.commit()

        db.refresh(product)
        db.refresh(specialized)

        return product

    except (SQLAlchemyError, ValueError):
        db.rollback()
        raise


# ============================================================
# PRODUCT STATUS
# ============================================================


def set_product_status(
    db: Session,
    product: Product,
    is_active: bool,
) -> Product:
    """
    Activate or deactivate a product.

    Products are not hard-deleted because they may already
    belong to packages or historical quotations.
    """

    try:
        product.is_active = is_active

        db.commit()
        db.refresh(product)

        return product

    except SQLAlchemyError:
        db.rollback()
        raise
