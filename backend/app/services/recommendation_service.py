"""
Solar Recommendation Engine
============================

Selects and ranks suitable solar packages using verified SQL Server data.

Two outputs are intentionally separated:
1. recommend_packages() -> commercially suitable recommendations.
2. find_closest_alternatives() -> nearest catalog options when no suitable
   recommendation exists. Alternatives are NEVER labelled recommendations.
"""

from app.models.package_item import PackageItem
from app.models.product import Product
from app.models.solar_package import SolarPackage
from app.schemas.recommendation import RecommendationRequest
from sqlalchemy.orm import Session

MAX_OVERSIZE_RATIO = 1.50
MIN_SIZE_RATIO = 0.90
MAX_OVER_BUDGET_RATIO = 0.50


def _base_package_query(db: Session, requirements: RecommendationRequest):
    query = db.query(SolarPackage).filter(SolarPackage.is_active == 1)

    if requirements.needs_backup is True:
        query = (
            query.join(PackageItem, PackageItem.package_id == SolarPackage.id)
            .join(Product, Product.id == PackageItem.product_id)
            .filter(Product.category == "battery")
        )

    return query.distinct()


def _score_package(package, requirements: RecommendationRequest) -> dict:
    score = 0.0
    reasons: list[str] = []

    # System type: 30
    if requirements.system_type:
        if package.system_type.lower() == requirements.system_type.lower():
            score += 30
            reasons.append("Matches the requested system type.")
        else:
            reasons.append("System type differs from the requested type.")
    else:
        score += 30
        reasons.append("No specific system type was required.")

    # System size: 50
    if requirements.required_kw is not None and requirements.required_kw > 0:
        required_kw = float(requirements.required_kw)
        package_kw = float(package.system_size_kw)
        difference = abs(package_kw - required_kw)
        percentage_difference = difference / required_kw
        score += max(0, 50 * (1 - percentage_difference))

        if difference < 0.01:
            reasons.append("Exactly matches the requested system size.")
        elif package_kw > required_kw:
            reasons.append(
                f"System size is {difference:.1f} kW above the requested capacity."
            )
        else:
            reasons.append(
                f"System size is {difference:.1f} kW below the requested capacity."
            )
    else:
        score += 50
        reasons.append("No specific system size was required.")

    # Budget: 20
    if requirements.budget is not None and requirements.budget > 0:
        budget = float(requirements.budget)
        package_price = float(package.package_price)
        difference = budget - package_price

        if difference >= 0:
            savings_ratio = difference / budget
            score += min(20, 15 + (5 * savings_ratio))
            if difference < 1:
                reasons.append("Package matches the customer's budget.")
            else:
                reasons.append(f"Within budget with PKR {difference:,.0f} remaining.")
        else:
            over_budget = abs(difference)
            over_budget_ratio = over_budget / budget
            score += max(0, 15 * (1 - (over_budget_ratio * 2)))
            reasons.append(f"Exceeds the customer's budget by PKR {over_budget:,.0f}.")
    else:
        score += 20
        reasons.append("No maximum budget was specified.")

    if requirements.needs_backup is True:
        reasons.append("Includes a battery for the backup requirement.")

    return {
        "package": package,
        "match_score": min(100, round(score, 2)),
        "reasons": reasons,
    }


def recommend_packages(
    db: Session,
    requirements: RecommendationRequest,
) -> list[dict]:
    """
    Return only commercially reasonable packages.

    Guardrails:
    - active package
    - battery included when backup is required
    - 90% to 150% of required capacity
    - no more than 50% above stated budget
    """
    packages = _base_package_query(db, requirements).all()
    recommendations: list[dict] = []

    for package in packages:
        if requirements.required_kw is not None and requirements.required_kw > 0:
            required_kw = float(requirements.required_kw)
            size_ratio = float(package.system_size_kw) / required_kw

            if size_ratio < MIN_SIZE_RATIO or size_ratio > MAX_OVERSIZE_RATIO:
                continue

        if requirements.budget is not None and requirements.budget > 0:
            budget = float(requirements.budget)
            package_price = float(package.package_price)

            if package_price > budget:
                over_budget_ratio = (package_price - budget) / budget
                if over_budget_ratio > MAX_OVER_BUDGET_RATIO:
                    continue

        recommendations.append(_score_package(package, requirements))

    recommendations.sort(
        key=lambda result: result["match_score"],
        reverse=True,
    )
    return recommendations


def find_closest_alternatives(
    db: Session,
    requirements: RecommendationRequest,
    limit: int = 2,
) -> list[dict]:
    """
    Return nearest catalog options for explanation when recommend_packages()
    returns nothing.

    IMPORTANT:
    These are alternatives, not recommendations. The strict commercial
    guardrails are intentionally not applied here, but active-package and
    requested-battery constraints are retained.

    Ranking prioritizes:
    1. capacity distance
    2. budget distance
    3. system-type mismatch
    """
    packages = _base_package_query(db, requirements).all()
    alternatives: list[dict] = []

    for package in packages:
        reasons: list[str] = []
        distance = 0.0

        if requirements.required_kw is not None and requirements.required_kw > 0:
            required_kw = float(requirements.required_kw)
            package_kw = float(package.system_size_kw)
            size_difference = package_kw - required_kw
            size_ratio_difference = abs(size_difference) / required_kw

            # Size is the most important alternative-distance factor.
            distance += size_ratio_difference * 60

            if abs(size_difference) < 0.01:
                reasons.append("Capacity matches the requested system size.")
            elif size_difference > 0:
                reasons.append(
                    f"Capacity is {size_difference:.1f} kW above your requirement."
                )
            else:
                reasons.append(
                    f"Capacity is {abs(size_difference):.1f} kW below your requirement."
                )

        if requirements.budget is not None and requirements.budget > 0:
            budget = float(requirements.budget)
            package_price = float(package.package_price)
            price_difference = package_price - budget
            price_ratio_difference = abs(price_difference) / budget

            distance += min(price_ratio_difference, 5) * 30

            if abs(price_difference) < 1:
                reasons.append("Price matches your stated budget.")
            elif price_difference > 0:
                reasons.append(
                    f"Price is PKR {price_difference:,.0f} above your budget."
                )
            else:
                reasons.append(
                    f"Price is PKR {abs(price_difference):,.0f} within your budget."
                )

        if requirements.system_type:
            if package.system_type.lower() != requirements.system_type.lower():
                distance += 10
                reasons.append(
                    f"Package type is {package.system_type}, not "
                    f"{requirements.system_type}."
                )
            else:
                reasons.append("System type matches your requirement.")

        if requirements.needs_backup is True:
            reasons.append("Includes battery backup as requested.")

        alternatives.append(
            {
                "package": package,
                "distance_score": round(distance, 2),
                "reasons": reasons,
            }
        )

    alternatives.sort(key=lambda item: item["distance_score"])
    return alternatives[: max(1, limit)]
