"""
Chat Service
============

Persistent conversation memory, appliance memory, contextual extraction,
CRM conversion, and strict phone/budget validation.
"""

import json
import re

import phonenumbers
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.lead import Lead
from app.schemas.agent import AgentExtraction, ApplianceUsage
from app.schemas.lead import LeadCreate
from app.services.lead_service import create_lead
from app.services.qualification_service import qualify_lead
from app.services.solar_sizing_service import normalize_appliance_name
from phonenumbers import NumberParseException
from sqlalchemy.orm import Session


def create_chat_session(db: Session) -> ChatSession:
    chat_session = ChatSession()
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def normalize_pakistani_mobile(phone: str | None) -> str | None:
    """
    Validate international phone numbers and return E.164.
    Pakistani local 03XXXXXXXXX is accepted for convenience.
    """
    if not phone:
        return None

    cleaned = re.sub(r"[\s\-().]", "", str(phone).strip())

    if re.fullmatch(r"03\d{9}", cleaned):
        cleaned = "+92" + cleaned[1:]

    if not cleaned.startswith("+"):
        return None

    try:
        parsed = phonenumbers.parse(cleaned, None)
        if not phonenumbers.is_possible_number(parsed):
            return None
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.E164,
        )
    except NumberParseException:
        return None


def is_safe_budget(value: float | str | None) -> bool:
    if value is None:
        return False
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False
    if amount <= 0:
        return False
    if amount.is_integer():  # noqa: SIM102
        if normalize_pakistani_mobile(str(int(amount))) is not None:
            return False
    return 50_000 <= amount <= 100_000_000


def _load_appliances(session: ChatSession) -> list[ApplianceUsage]:
    if not session.appliance_usage_json:
        return []
    try:
        raw = json.loads(session.appliance_usage_json)
        if not isinstance(raw, list):
            return []
        return [ApplianceUsage.model_validate(item) for item in raw]
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def _save_appliances(
    session: ChatSession,
    appliances: list[ApplianceUsage],
) -> None:
    session.appliance_usage_json = json.dumps(
        [item.model_dump() for item in appliances],
        ensure_ascii=False,
    )


def _canonical_appliance(name: str) -> str:
    normalized = normalize_appliance_name(name)
    aliases = {
        "air_conditioner": "ac",
        "airconditioner": "ac",
        "a_c": "ac",
        "ceiling_fan": "fan",
        "refrigerator": "fridge",
        "led_light": "light",
        "bulb": "light",
        "television": "tv",
        "desktop": "computer",
    }
    return aliases.get(normalized, normalized)


def merge_appliances(
    existing: list[ApplianceUsage],
    incoming: list[ApplianceUsage],
) -> list[ApplianceUsage]:
    """
    Merge appliance details across messages.

    Same canonical appliance is updated rather than duplicated.
    Incoming non-null details win. Quantity is replaced when the
    latest message explicitly contains that appliance entry.
    """
    merged = [item.model_copy(deep=True) for item in existing]
    positions = {
        _canonical_appliance(item.appliance): index for index, item in enumerate(merged)
    }

    for new_item in incoming:
        key = _canonical_appliance(new_item.appliance)
        normalized_new = new_item.model_copy(deep=True)
        normalized_new.appliance = key

        if key not in positions:
            positions[key] = len(merged)
            merged.append(normalized_new)
            continue

        current = merged[positions[key]]
        current.quantity = normalized_new.quantity

        if normalized_new.wattage is not None:
            current.wattage = normalized_new.wattage
        if normalized_new.hours_per_day is not None:
            current.hours_per_day = normalized_new.hours_per_day
        if normalized_new.capacity_ton is not None:
            current.capacity_ton = normalized_new.capacity_ton

    return merged


def get_pending_appliance(appliances: list[ApplianceUsage]) -> tuple[str, str] | None:
    """
    Return (canonical appliance name, missing field) for the first
    important detail that requires a customer follow-up.
    """
    for item in appliances:
        key = _canonical_appliance(item.appliance)

        if key == "ac":
            if item.wattage is None and item.capacity_ton is None:
                return key, "capacity_ton"
            if item.hours_per_day is None:
                return key, "hours_per_day"

    return None


def apply_appliance_followup(
    session: ChatSession,
    extracted: AgentExtraction,
    message: str,
) -> bool:
    """
    Interpret a short numeric reply using appliance context BEFORE
    the old kW/budget numeric fallback.

    Returns True when the message was consumed as appliance detail.
    """
    appliances = _load_appliances(session)
    pending = get_pending_appliance(appliances)

    if pending is None:
        return False

    key, missing_field = pending
    clean = message.strip().lower()

    number_match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|ghantay|ghante|ton)?\s*",
        clean,
    )
    if not number_match:
        return False

    value = float(number_match.group(1))

    for item in appliances:
        if _canonical_appliance(item.appliance) != key:
            continue

        if missing_field == "capacity_ton" and 0.5 <= value <= 10:
            item.capacity_ton = value
        elif missing_field == "hours_per_day" and 0 <= value <= 24:
            item.hours_per_day = value
        else:
            return False

        _save_appliances(session, appliances)

        # Prevent the same numeric message becoming kW/budget.
        extracted.required_kw = None
        extracted.budget = None
        return True

    return False


def apply_contextual_crm_fallback(
    session: ChatSession,
    extracted: AgentExtraction,
    message: str,
) -> AgentExtraction:
    clean_message = message.strip()
    if not clean_message:
        return extracted

    lower_message = clean_message.lower()

    # Appliance follow-up gets priority over generic numeric interpretation.
    if apply_appliance_followup(session, extracted, clean_message):
        return extracted

    if (
        session.required_kw is None
        and extracted.required_kw is None
        and not _load_appliances(session)
        and session.monthly_units is None
    ):
        try:
            value = float(clean_message.replace(",", ""))
            if 0.5 <= value <= 1000:
                extracted.required_kw = value
                return extracted
        except ValueError:
            pass

    current_kw = (
        extracted.required_kw
        if extracted.required_kw is not None
        else session.required_kw
    )

    if (
        current_kw is not None
        and session.budget is None
        and extracted.budget is None
        and normalize_pakistani_mobile(clean_message) is None
    ):
        try:
            value = float(clean_message.replace(",", "").replace(" ", ""))
            if is_safe_budget(value):
                extracted.budget = value
                return extracted
        except ValueError:
            pass

    current_budget = (
        extracted.budget if extracted.budget is not None else session.budget
    )

    if (
        current_kw is not None
        and current_budget is not None
        and session.needs_backup is None
        and extracted.needs_backup is None
    ):
        yes_answers = {
            "yes",
            "yes please",
            "y",
            "han",
            "haan",
            "ha",
            "g",
            "g han",
            "g haan",
            "ji",
            "ji han",
            "ji haan",
            "chahiye",
            "chahye",
            "required",
            "need",
            "i need it",
        }
        no_answers = {
            "no",
            "n",
            "nope",
            "nahi",
            "nai",
            "nahin",
            "nhi",
            "nahi chahiye",
            "nai chahiye",
            "not required",
            "without battery",
            "without backup",
        }
        if lower_message in yes_answers:
            extracted.needs_backup = True
            return extracted
        if lower_message in no_answers:
            extracted.needs_backup = False
            return extracted

    current_sales_intent = (
        extracted.wants_sales_contact
        if extracted.wants_sales_contact is not None
        else session.wants_sales_contact
    )
    current_quotation_intent = (
        extracted.wants_quotation
        if extracted.wants_quotation is not None
        else session.wants_quotation
    )

    if current_quotation_intent is True:
        current_sales_intent = True
        extracted.wants_sales_contact = True

    if (
        current_sales_intent is True
        and not session.customer_name
        and extracted.name is None
    ):
        looks_like_phone = any(ch.isdigit() for ch in clean_message)
        looks_like_email = "@" in clean_message
        words = clean_message.split()
        non_name_keywords = {
            "quotation",
            "qoutation",
            "quote",
            "proposal",
            "contact",
            "sales",
            "team",
            "call",
            "phone",
            "number",
            "package",
            "solar",
            "system",
            "price",
            "budget",
            "buy",
            "purchase",
            "order",
            "recommend",
            "recommendation",
            "mujay",
            "mujhe",
            "mera",
            "meri",
            "chahiye",
            "chahye",
            "chahta",
            "chahti",
            "do",
            "kar",
            "karo",
            "kare",
            "karein",
            "proceed",
        }
        message_words = {word.strip(".,!?;:'\"()[]{}").lower() for word in words}
        allowed = all(
            ch.isalpha() or ch.isspace() or ch in {"-", "'", "."}
            for ch in clean_message
        )
        if (
            not looks_like_phone
            and not looks_like_email
            and not (message_words & non_name_keywords)
            and allowed
            and 1 <= len(words) <= 5
            and len(clean_message) <= 100
        ):
            extracted.name = clean_message
            return extracted

    current_name = (
        extracted.name if extracted.name is not None else session.customer_name
    )
    if current_sales_intent is True and current_name and not session.customer_phone:
        valid_phone = normalize_pakistani_mobile(extracted.phone or clean_message)
        extracted.phone = valid_phone
        if valid_phone:
            return extracted

    return extracted


def merge_agent_data(
    session: ChatSession,
    extracted: AgentExtraction,
) -> None:
    if extracted.budget is not None:
        if is_safe_budget(extracted.budget):
            session.budget = float(extracted.budget)
        else:
            extracted.budget = None

    if extracted.required_kw is not None:
        session.required_kw = extracted.required_kw
    if extracted.system_type is not None:
        session.system_type = extracted.system_type
    if extracted.needs_backup is not None:
        session.needs_backup = extracted.needs_backup
    if extracted.monthly_units is not None and extracted.monthly_units > 0:
        session.monthly_units = float(extracted.monthly_units)

    if extracted.appliances:
        merged = merge_appliances(
            _load_appliances(session),
            extracted.appliances,
        )
        _save_appliances(session, merged)

    if extracted.name is not None:
        session.customer_name = extracted.name

    if extracted.phone is not None:
        valid_phone = normalize_pakistani_mobile(extracted.phone)
        if valid_phone:
            session.customer_phone = valid_phone

    if extracted.email is not None:
        session.customer_email = extracted.email
    if extracted.city is not None:
        session.customer_city = extracted.city
    if extracted.wants_sales_contact is not None:
        session.wants_sales_contact = extracted.wants_sales_contact
    if extracted.wants_quotation is not None:
        session.wants_quotation = extracted.wants_quotation

    if session.wants_quotation is True:
        session.wants_sales_contact = True


def get_session_agent_data(session: ChatSession) -> AgentExtraction:
    safe_budget = session.budget if is_safe_budget(session.budget) else None

    return AgentExtraction(
        budget=safe_budget,
        required_kw=session.required_kw,
        system_type=session.system_type,
        needs_backup=session.needs_backup,
        monthly_units=session.monthly_units,
        appliances=_load_appliances(session),
        wants_sales_contact=session.wants_sales_contact,
        wants_quotation=session.wants_quotation,
        name=session.customer_name,
        phone=session.customer_phone,
        email=session.customer_email,
        city=session.customer_city,
    )


def get_chat_session(db: Session, session_id: int) -> ChatSession | None:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def save_chat_message(
    db: Session,
    session_id: int,
    customer_message: str,
    assistant_message: str,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        customer_message=customer_message,
        assistant_message=assistant_message,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_chat_history(db: Session, session_id: int) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )


def create_lead_from_chat(
    db: Session,
    session: ChatSession,
) -> Lead | None:
    if session.wants_sales_contact is not True:
        return None
    if not session.customer_name:
        return None

    valid_phone = normalize_pakistani_mobile(session.customer_phone)
    if valid_phone is None:
        session.customer_phone = None
        db.commit()
        db.refresh(session)
        return None

    session.customer_phone = valid_phone

    if session.lead_id is not None:
        return None

    interested_system = None
    if session.required_kw is not None:
        interested_system = f"{session.required_kw:g} kW"
    if session.system_type:
        interested_system = (
            f"{interested_system} {session.system_type}"
            if interested_system
            else session.system_type
        )

    safe_budget = (
        float(session.budget)
        if session.budget is not None and is_safe_budget(session.budget)
        else None
    )

    if session.budget is not None and safe_budget is None:
        session.budget = None
        db.commit()
        db.refresh(session)

    lead_data = LeadCreate(
        name=session.customer_name,
        phone=valid_phone,
        email=session.customer_email,
        city=session.customer_city,
        monthly_bill=None,
        interested_system=interested_system,
        budget=safe_budget,
        source="ai_agent",
    )

    qualification = qualify_lead(session)
    lead = create_lead(db=db, lead_data=lead_data)
    lead.qualification_score = qualification.score
    lead.qualification_level = qualification.level

    db.commit()
    db.refresh(lead)

    session.lead_id = lead.id
    db.commit()
    db.refresh(session)
    return lead
