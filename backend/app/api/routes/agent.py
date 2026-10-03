"""
AI Solar Sales Agent API
========================

Flow:
Customer -> Session -> Classification -> Extraction -> persistent memory
-> deterministic sizing -> CRM -> recommendation -> optional quotation
-> save conversation -> response
"""

from typing import Annotated

from app.database.database import get_db
from app.models.lead import Lead
from app.models.proposal import Proposal
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentQuotation,
    ChatHistoryResponse,
    ExtractedRequirements,
)
from app.schemas.lead import LeadStatus, LeadUpdate
from app.schemas.proposal import ProposalCreate
from app.schemas.recommendation import RecommendationRequest
from app.services.ai_service import (
    answer_general_question,
    classify_customer_message,
    detect_customer_language,
    extract_agent_data,
    generate_sales_reply,
    localized_text,
)
from app.services.chat_service import (
    apply_contextual_crm_fallback,
    create_chat_session,
    create_lead_from_chat,
    get_chat_history,
    get_chat_session,
    get_pending_appliance,
    get_session_agent_data,
    merge_agent_data,
    normalize_pakistani_mobile,
    save_chat_message,
)
from app.services.lead_service import (
    update_lead,
    validate_status_transition,
)
from app.services.proposal_service import (
    create_proposal,
    get_existing_proposal_for_lead_package,
)
from app.services.qualification_service import update_lead_qualification
from app.services.recommendation_service import (
    find_closest_alternatives,
    recommend_packages,
)
from app.services.solar_sizing_service import (
    estimate_from_appliances,
    estimate_from_monthly_units,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/agent", tags=["AI Sales Agent"])


def resolve_session_language(chat_session, message: str) -> str:
    """
    Preserve conversation language for short follow-ups such as
    '6', 'yes', phone numbers and names.
    """
    detected = detect_customer_language(message)

    if chat_session.preferred_language:
        words = message.strip().split()
        short_or_numeric = (
            len(words) <= 2 or message.strip().replace(".", "", 1).isdigit()
        )
        if short_or_numeric:
            return chat_session.preferred_language

    chat_session.preferred_language = detected
    return detected


def advance_lead_to_proposal_stage(db: Session, lead: Lead) -> Lead:
    path = {
        "new": LeadStatus.CONTACTED,
        "contacted": LeadStatus.QUALIFIED,
        "qualified": LeadStatus.PROPOSAL,
    }
    while lead.status in path:
        next_status = path[lead.status]
        if not validate_status_transition(lead.status, next_status):
            break
        lead = update_lead(
            db=db,
            lead=lead,
            lead_data=LeadUpdate(status=next_status),
        )
    return lead


def build_quotation_response(proposal: Proposal) -> AgentQuotation:
    return AgentQuotation(
        proposal_id=proposal.id,
        proposal_number=proposal.proposal_number,
        package_id=proposal.package_id,
        status=proposal.status,
        subtotal=float(proposal.subtotal),
        discount=float(proposal.discount),
        total_price=float(proposal.total_price),
        pdf_url=f"/api/proposals/{proposal.id}/pdf",
    )


def _response(
    chat_session,
    request,
    agent_data,
    reply,
    sizing=None,
    recommendations=None,
    quotation=None,
):
    return {
        "session_id": chat_session.id,
        "customer_message": request.message,
        "extracted_requirements": agent_data,
        "lead_id": chat_session.lead_id,
        "reply": reply,
        "sizing": sizing,
        "recommendations": recommendations or [],
        "quotation": quotation,
    }


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatHistoryResponse,
)
def read_chat_history(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    chat_session = get_chat_session(db, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    return {
        "session_id": chat_session.id,
        "messages": get_chat_history(db, session_id),
    }


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_sales_agent(
    request: AgentChatRequest,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        # 1. Session
        if request.session_id is None:
            chat_session = create_chat_session(db)
        else:
            chat_session = get_chat_session(db, request.session_id)
            if chat_session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found.",
                )

        language = resolve_session_language(chat_session, request.message)
        db.commit()
        db.refresh(chat_session)

        # 2. General question vs sales conversation.
        message_type = classify_customer_message(request.message)

        if message_type == "general_question":
            try:
                reply = answer_general_question(request.message)
            except Exception as error:  # noqa: BLE001
                print("GENERAL QUESTION ERROR:", repr(error))
                reply = localized_text(
                    language,
                    "Maazrat, main is sawal ka jawab abhi generate nahi kar pa raha. Dobara try karein.",
                    "Sorry, I could not generate an answer right now. Please try again.",
                )

            save_chat_message(
                db,
                chat_session.id,
                request.message,
                reply,
            )
            return _response(
                chat_session,
                request,
                get_session_agent_data(chat_session),
                reply,
            )

        # 3. Extract current message and apply contextual fallback.
        extracted = extract_agent_data(request.message)
        extracted = apply_contextual_crm_fallback(
            chat_session,
            extracted,
            request.message,
        )

        # 4. Merge persistent memory.
        merge_agent_data(chat_session, extracted)
        db.commit()
        db.refresh(chat_session)
        agent_data = get_session_agent_data(chat_session)

        # 5. Ask for critical appliance detail before sizing.
        pending = get_pending_appliance(agent_data.appliances)

        if (
            agent_data.required_kw is None
            and agent_data.monthly_units is None
            and pending is not None
        ):
            appliance_name, missing_field = pending

            if appliance_name == "ac" and missing_field == "capacity_ton":
                reply = localized_text(
                    language,
                    "AC kitne ton ka hai? Misal ke taur par 1 ton, 1.5 ton ya 2 ton.",
                    "What is the AC capacity? For example 1 ton, 1.5 ton, or 2 ton.",
                )
            elif appliance_name == "ac" and missing_field == "hours_per_day":
                reply = localized_text(
                    language,
                    "AC approximately roz kitne hours chalega?",
                    "Approximately how many hours per day will the AC run?",
                )
            else:
                reply = localized_text(
                    language,
                    f"{appliance_name} ki wattage ya daily usage hours share kar dein.",
                    f"Please share the wattage or daily usage hours for {appliance_name}.",
                )

            save_chat_message(db, chat_session.id, request.message, reply)
            return _response(chat_session, request, agent_data, reply)

        # 6. Deterministic preliminary sizing.
        sizing = None

        if agent_data.required_kw is None:
            if agent_data.appliances:
                sizing = estimate_from_appliances(
                    agent_data.appliances,
                    agent_data.needs_backup,
                )
            elif agent_data.monthly_units is not None:
                sizing = estimate_from_monthly_units(agent_data.monthly_units)

            if sizing is not None:
                chat_session.required_kw = sizing.recommended_system_kw
                db.commit()
                db.refresh(chat_session)
                agent_data = get_session_agent_data(chat_session)

        # 7. CRM contact flow.
        if agent_data.wants_sales_contact is True:
            if not agent_data.name:
                reply = localized_text(
                    language,
                    (
                        "Bilkul. Quotation tayar karne ke liye apna naam share kar dein?"
                        if agent_data.wants_quotation is True
                        else "Bilkul. Sales request register karne ke liye apna naam share kar dein?"
                    ),
                    (
                        "Sure. Please share your name so I can prepare the quotation."
                        if agent_data.wants_quotation is True
                        else "Sure. Please share your name so I can register the sales request."
                    ),
                )
                save_chat_message(db, chat_session.id, request.message, reply)
                return _response(chat_session, request, agent_data, reply, sizing)

            if not agent_data.phone:
                reply = localized_text(
                    language,
                    f"Thanks {agent_data.name}. Ab valid mobile number country code ke sath share kar dein, misal +923001234567.",
                    f"Thanks {agent_data.name}. Please share a valid phone number with country code, for example +923001234567.",
                )
                save_chat_message(db, chat_session.id, request.message, reply)
                return _response(chat_session, request, agent_data, reply, sizing)

            valid_phone = normalize_pakistani_mobile(agent_data.phone)

            if valid_phone is None:
                chat_session.customer_phone = None
                db.commit()
                db.refresh(chat_session)
                agent_data = get_session_agent_data(chat_session)

                reply = localized_text(
                    language,
                    "Ye phone number valid nahi lag raha. Pakistan local 03XXXXXXXXX ya international +countrycode number share karein.",
                    "That phone number does not appear valid. Please share a Pakistani 03XXXXXXXXX number or an international +countrycode number.",
                )
                save_chat_message(db, chat_session.id, request.message, reply)
                return _response(chat_session, request, agent_data, reply, sizing)

            if chat_session.customer_phone != valid_phone:
                chat_session.customer_phone = valid_phone
                db.commit()
                db.refresh(chat_session)
                agent_data = get_session_agent_data(chat_session)

            if chat_session.lead_id is None:
                lead = create_lead_from_chat(db, chat_session)
                if lead is not None:
                    db.refresh(chat_session)
                    agent_data = get_session_agent_data(chat_session)

        # 8. Collect remaining solar requirements.
        if agent_data.required_kw is None:
            if not agent_data.appliances and agent_data.monthly_units is None:
                reply = localized_text(
                    language,
                    (
                        "Aap apne appliances bata dein (misal AC, fans, fridge) "
                        "ya monthly electricity units share kar dein. Agar kW already pata hai to woh bhi bata sakte hain."
                    ),
                    (
                        "Please tell me the appliances you want to run (for example AC, fans, fridge) "
                        "or your monthly electricity units. If you already know the required kW, you can share that instead."
                    ),
                )
            else:
                reply = localized_text(
                    language,
                    "Sizing ke liye abhi kuch usage information missing hai.",
                    "Some usage information is still missing for preliminary sizing.",
                )
            save_chat_message(db, chat_session.id, request.message, reply)
            return _response(chat_session, request, agent_data, reply, sizing)

        if agent_data.budget is None:
            reply = localized_text(
                language,
                "Aapka approximate budget kitna hai?",
                "What is your approximate budget?",
            )
            save_chat_message(db, chat_session.id, request.message, reply)
            return _response(chat_session, request, agent_data, reply, sizing)

        if agent_data.needs_backup is None:
            reply = localized_text(
                language,
                "Kya aapko battery backup bhi chahiye?",
                "Do you also need battery backup?",
            )
            save_chat_message(db, chat_session.id, request.message, reply)
            return _response(chat_session, request, agent_data, reply, sizing)

        # 9. Recommendation engine.
        recommendation_request = RecommendationRequest(
            budget=agent_data.budget,
            required_kw=agent_data.required_kw,
            system_type=agent_data.system_type,
            needs_backup=agent_data.needs_backup,
        )

        sales_requirements = ExtractedRequirements(
            budget=agent_data.budget,
            required_kw=agent_data.required_kw,
            system_type=agent_data.system_type,
            needs_backup=agent_data.needs_backup,
            monthly_units=agent_data.monthly_units,
            appliances=agent_data.appliances,
        )

        recommendations = recommend_packages(
            db=db,
            requirements=recommendation_request,
        )

        if not recommendations:
            # No-match recovery:
            # Find the nearest active catalog option for explanation only.
            # It is NOT returned in recommendations and is NOT eligible for
            # automatic quotation generation.
            alternatives = find_closest_alternatives(
                db=db,
                requirements=recommendation_request,
                limit=1,
            )

            requirement_summary = localized_text(
                language,
                (
                    f"Aapki current requirement {agent_data.required_kw:g} kW "
                    f"aur budget PKR {agent_data.budget:,.0f} hai. "
                ),
                (
                    f"Your current requirement is {agent_data.required_kw:g} kW "
                    f"with a budget of PKR {agent_data.budget:,.0f}. "
                ),
            )

            if alternatives:
                alternative = alternatives[0]
                package = alternative["package"]

                # Build customer-facing reasons in the active conversation
                # language instead of exposing internal English reason strings.
                reason_parts: list[str] = []

                if agent_data.required_kw is not None and agent_data.required_kw > 0:
                    size_difference = float(package.system_size_kw) - float(
                        agent_data.required_kw
                    )

                    if abs(size_difference) < 0.01:
                        reason_parts.append(
                            localized_text(
                                language,
                                "capacity aapki requirement ke barabar hai",
                                "capacity matches your requirement",
                            )
                        )
                    elif size_difference > 0:
                        reason_parts.append(
                            localized_text(
                                language,
                                f"capacity {size_difference:.1f} kW zyada hai",
                                f"capacity is {size_difference:.1f} kW above your requirement",
                            )
                        )
                    else:
                        reason_parts.append(
                            localized_text(
                                language,
                                f"capacity {abs(size_difference):.1f} kW kam hai",
                                f"capacity is {abs(size_difference):.1f} kW below your requirement",
                            )
                        )

                if agent_data.budget is not None and agent_data.budget > 0:
                    price_difference = float(package.package_price) - float(
                        agent_data.budget
                    )

                    if abs(price_difference) < 1:
                        reason_parts.append(
                            localized_text(
                                language,
                                "price aapke budget ke barabar hai",
                                "price matches your budget",
                            )
                        )
                    elif price_difference > 0:
                        reason_parts.append(
                            localized_text(
                                language,
                                f"price budget se PKR {price_difference:,.0f} zyada hai",
                                f"price is PKR {price_difference:,.0f} above your budget",
                            )
                        )
                    else:
                        reason_parts.append(
                            localized_text(
                                language,
                                f"price budget se PKR {abs(price_difference):,.0f} kam hai",
                                f"price is PKR {abs(price_difference):,.0f} within your budget",
                            )
                        )

                if (
                    agent_data.system_type
                    and package.system_type.lower() != agent_data.system_type.lower()
                ):
                    reason_parts.append(
                        localized_text(
                            language,
                            (
                                f"package {package.system_type} type ka hai jab ke "
                                f"aapne {agent_data.system_type} manga hai"
                            ),
                            (
                                f"the package is {package.system_type}, while "
                                f"you requested {agent_data.system_type}"
                            ),
                        )
                    )

                if agent_data.needs_backup is True:
                    reason_parts.append(
                        localized_text(
                            language,
                            "is package mein battery backup included hai",
                            "battery backup is included",
                        )
                    )

                reason_text = "; ".join(reason_parts)

                reply = localized_text(
                    language,
                    (
                        f"{requirement_summary}"
                        "Current catalog mein abhi koi suitable package nahi mila.\n\n"
                        f"Nearest option: {package.name}\n"
                        f"System: {package.system_size_kw:g} kW {package.system_type}\n"
                        f"Demo price: PKR {package.package_price:,.0f}\n\n"
                        "Ye sirf closest alternative hai, recommendation nahi. "
                        f"Wajah: {reason_text}.\n\n"
                        "Aap budget, required kW ya battery backup requirement change kar sakte hain. "
                        "Custom quotation ke liye sales contact bhi request kar sakte hain."
                    ),
                    (
                        f"{requirement_summary}"
                        "There is currently no suitable package in the catalog.\n\n"
                        f"Nearest option: {package.name}\n"
                        f"System: {package.system_size_kw:g} kW {package.system_type}\n"
                        f"Demo price: PKR {package.package_price:,.0f}\n\n"
                        "This is only the closest alternative, not a recommendation. "
                        f"Reason: {reason_text}.\n\n"
                        "You can change the budget, required kW, or battery-backup requirement. "
                        "You can also request sales contact for a custom quotation."
                    ),
                )
            else:
                backup_note = localized_text(
                    language,
                    (
                        " Battery backup requirement ki wajah se eligible catalog options bhi available nahi hain."
                        if agent_data.needs_backup is True
                        else ""
                    ),
                    (
                        " There are also no eligible catalog options under the battery-backup requirement."
                        if agent_data.needs_backup is True
                        else ""
                    ),
                )

                reply = localized_text(
                    language,
                    (
                        f"{requirement_summary}Current catalog mein suitable package nahi mila."
                        f"{backup_note} Aap budget, required kW ya backup requirement change kar sakte hain, "
                        "ya custom quotation ke liye sales contact request kar sakte hain."
                    ),
                    (
                        f"{requirement_summary}No suitable package is available in the current catalog."
                        f"{backup_note} You can change the budget, required kW or backup requirement, "
                        "or request sales contact for a custom quotation."
                    ),
                )

            save_chat_message(db, chat_session.id, request.message, reply)
            return _response(chat_session, request, agent_data, reply, sizing)

        recommendation_data = []
        for result in recommendations:
            package = result["package"]
            recommendation_data.append(
                {
                    "package_id": package.id,
                    "name": package.name,
                    "system_size_kw": package.system_size_kw,
                    "system_type": package.system_type,
                    "package_price": package.package_price,
                    "match_score": result["match_score"],
                    "reasons": result["reasons"],
                }
            )

        best = recommendation_data[0]

        # 10. CRM qualification.
        if chat_session.lead_id is not None:
            lead = db.get(Lead, chat_session.lead_id)
            if lead is not None:
                update_lead_qualification(
                    db=db,
                    lead=lead,
                    session=chat_session,
                    recommendation=best,
                )

        # 11. Quotation only when explicitly requested.
        quotation = None
        if agent_data.wants_quotation is True and chat_session.lead_id is not None:
            proposal = get_existing_proposal_for_lead_package(
                db=db,
                lead_id=chat_session.lead_id,
                package_id=best["package_id"],
            )

            if proposal is None:
                lead = db.get(Lead, chat_session.lead_id)
                if lead is not None:
                    advance_lead_to_proposal_stage(db, lead)

                proposal = create_proposal(
                    db=db,
                    proposal_data=ProposalCreate(
                        lead_id=chat_session.lead_id,
                        package_id=best["package_id"],
                        discount=0,
                        notes=(
                            "Automatically generated from the AI Sales Agent "
                            "using the highest-ranked verified package."
                        ),
                    ),
                )

            quotation = build_quotation_response(proposal)

        # 12. Customer-facing response.
        sizing_intro = ""
        if sizing is not None:
            sizing_intro = localized_text(
                language,
                (
                    f"Preliminary sizing ke mutabiq estimated daily usage "
                    f"{sizing.estimated_daily_energy_kwh:g} kWh hai aur "
                    f"recommended system approximately {sizing.recommended_system_kw:g} kW hai. "
                ),
                (
                    f"Based on preliminary sizing, estimated daily usage is "
                    f"{sizing.estimated_daily_energy_kwh:g} kWh and the recommended system is "
                    f"approximately {sizing.recommended_system_kw:g} kW. "
                ),
            )

        fallback_reply = localized_text(
            language,
            (
                f"{sizing_intro}{best['name']} best available match hai. "
                f"Ye {best['system_size_kw']} kW {best['system_type']} system hai "
                f"aur demo price PKR {best['package_price']:,.0f} hai."
            ),
            (
                f"{sizing_intro}{best['name']} is the best available match. "
                f"It is a {best['system_size_kw']} kW {best['system_type']} system "
                f"with a demo price of PKR {best['package_price']:,.0f}."
            ),
        )

        try:
            reply = generate_sales_reply(
                customer_message=request.message,
                requirements=sales_requirements,
                recommendation=best,
            )
            if sizing_intro:
                reply = sizing_intro + reply
        except Exception as error:  # noqa: BLE001
            print("SALES REPLY ERROR:", repr(error))
            reply = fallback_reply

        if quotation is not None:
            reply += localized_text(
                language,
                (
                    f" Aapki quotation {quotation.proposal_number} tayyar hai. "
                    f"Total PKR {quotation.total_price:,.0f} hai."
                ),
                (
                    f" Your quotation {quotation.proposal_number} is ready. "
                    f"Total: PKR {quotation.total_price:,.0f}."
                ),
            )

        save_chat_message(db, chat_session.id, request.message, reply)

        return _response(
            chat_session,
            request,
            agent_data,
            reply,
            sizing,
            recommendation_data,
            quotation,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        print("DATABASE ERROR:", repr(error))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while processing conversation.",
        ) from error
    except Exception as error:
        db.rollback()
        print("AGENT ERROR:", repr(error))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
