"""
Lead Qualification Service
==========================

Scores a customer using deterministic business rules.

No Gemini/LLM request is required.
"""

from app.models.chat_session import ChatSession
from app.schemas.qualification import LeadQualificationResult
from app.services.lead_activity_service import create_lead_activity

"""
Lead Qualification Service
==========================

Calculates a customer's sales-readiness score using
deterministic business rules.

The qualification engine can use:
1. Customer/session information
2. Sales intent
3. Solar requirements
4. Verified recommendation data

No additional Gemini/LLM request is required.
"""


def qualify_lead(
    session: ChatSession,
    recommendation: dict | None = None,
) -> LeadQualificationResult:
    """
    Calculate the lead qualification score.

    Args:
        session:
            Current customer chat session.

        recommendation:
            Optional verified recommendation returned by
            our recommendation engine.

    Returns:
        LeadQualificationResult containing:
        - score
        - level
        - reasons

    Maximum score: 100.
    """

    score = 0
    reasons: list[str] = []

    # --------------------------------------------------
    # 1. SALES INTENT — 20 POINTS
    # --------------------------------------------------

    if session.wants_sales_contact is True:
        score += 20
        reasons.append("Customer explicitly requested sales contact.")

    # --------------------------------------------------
    # 2. CONTACT DETAILS — 15 POINTS
    # --------------------------------------------------

    if session.customer_name and session.customer_phone:
        score += 15
        reasons.append("Customer name and phone number are available.")

    # --------------------------------------------------
    # 3. BUDGET — 15 POINTS
    # --------------------------------------------------

    if session.budget is not None:
        score += 15
        reasons.append("Customer budget is known.")

    # --------------------------------------------------
    # 4. REQUIRED SYSTEM SIZE — 10 POINTS
    # --------------------------------------------------

    if session.required_kw is not None:
        score += 10
        reasons.append("Required solar system size is known.")

    # --------------------------------------------------
    # 5. SOLAR REQUIREMENTS — 10 POINTS
    # --------------------------------------------------

    if session.system_type is not None and session.needs_backup is not None:
        score += 10
        reasons.append("System type and backup requirements are known.")

    # --------------------------------------------------
    # 6. SUITABLE PACKAGE FOUND — 15 POINTS
    # --------------------------------------------------

    if recommendation is not None:
        score += 15
        reasons.append("A suitable solar package was found.")

        # --------------------------------------------------
        # 7. PACKAGE WITHIN BUDGET — 15 POINTS
        # --------------------------------------------------

        package_price = recommendation.get("package_price")

        if (
            session.budget is not None
            and package_price is not None
            and package_price <= session.budget
        ):
            score += 15
            reasons.append("Recommended package is within customer budget.")

    # --------------------------------------------------
    # QUALIFICATION LEVEL
    # --------------------------------------------------

    if score >= 70:
        level = "hot"
    elif score >= 40:
        level = "warm"
    else:
        level = "cold"

    return LeadQualificationResult(
        score=score,
        level=level,
        reasons=reasons,
    )


def update_lead_qualification(
    db,
    lead,
    session: ChatSession,
    recommendation: dict | None = None,
) -> LeadQualificationResult:
    """
    Recalculate and persist a lead's qualification score.

    If the qualification score or level changes,
    a CRM timeline activity is also created.
    """

    # --------------------------------------------------
    # 1. SAVE OLD QUALIFICATION
    # --------------------------------------------------
    old_score = lead.qualification_score
    old_level = lead.qualification_level

    # --------------------------------------------------
    # 2. RECALCULATE QUALIFICATION
    # --------------------------------------------------
    qualification = qualify_lead(
        session=session,
        recommendation=recommendation,
    )

    new_score = qualification.score
    new_level = qualification.level.value

    # --------------------------------------------------
    # 3. CHECK WHETHER ANYTHING ACTUALLY CHANGED
    # --------------------------------------------------
    qualification_changed = old_score != new_score or old_level != new_level

    # --------------------------------------------------
    # 4. UPDATE LEAD
    # --------------------------------------------------
    lead.qualification_score = new_score
    lead.qualification_level = new_level

    db.commit()
    db.refresh(lead)

    # --------------------------------------------------
    # 5. RECORD CRM TIMELINE ACTIVITY
    # --------------------------------------------------
    # Do not create duplicate timeline entries when
    # qualification remains exactly the same.
    if qualification_changed:
        old_value = (
            f"{old_score} / {old_level}" if old_score is not None else "Not qualified"
        )

        new_value = f"{new_score} / {new_level}"

        create_lead_activity(
            db=db,
            lead_id=lead.id,
            activity_type="qualification_updated",
            description=(
                f"Lead qualification changed from {old_value} to {new_value}."
            ),
            old_value=old_value,
            new_value=new_value,
        )

    return qualification
