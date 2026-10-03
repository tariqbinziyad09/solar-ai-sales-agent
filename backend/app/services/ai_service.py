"""
AI Service
==========

Groq handles language understanding/extraction only.
Sizing, package selection, pricing, CRM and proposals remain deterministic.
"""

import json
import os
import re
import time

from app.schemas.agent import AgentExtraction, ApplianceUsage, ExtractedRequirements
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured in .env.")

client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL = "openai/gpt-oss-20b"

LANGUAGE_INSTRUCTIONS = """
LANGUAGE RULES:
- If customer writes Roman Urdu, reply in Roman Urdu.
- Roman Urdu must use Latin/English alphabet.
- NEVER use Hindi/Devanagari script for Roman Urdu.
- Simple English technical terms are allowed.
- If customer writes English, reply in English.
- Keep replies professional, natural and helpful.
"""


def detect_customer_language(message: str) -> str:
    text = message.lower().strip()
    roman_words = {
        "mujhe",
        "mujhay",
        "mujay",
        "mera",
        "meri",
        "meray",
        "aap",
        "hai",
        "hain",
        "han",
        "haan",
        "nahi",
        "nai",
        "chahiye",
        "chahye",
        "karna",
        "karo",
        "karein",
        "krna",
        "kitna",
        "kitni",
        "batao",
        "milega",
        "mujhse",
    }
    words = set(re.findall(r"[a-zA-Z]+", text))
    return "roman_urdu" if words & roman_words else "english"


def localized_text(language: str, roman_urdu: str, english: str) -> str:
    return roman_urdu if language == "roman_urdu" else english


def _extract_local_budget(message: str) -> float | None:
    text = message.lower()

    for pattern, multiplier in [
        (r"(?:budget|price|range|paas).{0,30}?(\d+(?:\.\d+)?)\s*(?:lakh|lac)", 100000),
        (r"(\d+(?:\.\d+)?)\s*(?:lakh|lac).{0,20}?(?:budget|range)", 100000),
        (r"(?:budget|price|range|paas).{0,30}?(\d+(?:\.\d+)?)\s*million", 1000000),
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1)) * multiplier

    match = re.search(
        r"(?:pkr|rs\.?|rupees?)\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE
    )
    if match:
        return float(match.group(1).replace(",", ""))

    return None


def _extract_local_kw(message: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kw|kilowatt)", message, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _extract_local_monthly_units(message: str) -> float | None:
    text = message.lower()
    patterns = [
        r"(?:monthly|month|mahina|mahinay|mahine).{0,25}?(\d+(?:\.\d+)?)\s*(?:units?|kwh)",
        r"(\d+(?:\.\d+)?)\s*(?:units?|kwh).{0,25}?(?:monthly|month|mahina|mahinay|mahine)",
        r"(?:bill|usage|consumption).{0,25}?(\d+(?:\.\d+)?)\s*(?:units?|kwh)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _extract_local_system_type(message: str) -> str | None:
    text = message.lower()
    if re.search(r"\bon[\s-]?grid\b", text):
        return "on-grid"
    if re.search(r"\boff[\s-]?grid\b", text):
        return "off-grid"
    if re.search(r"\bhybrid\b", text):
        return "hybrid"
    return None


def _extract_local_backup(message: str) -> bool | None:
    text = message.lower()
    if re.search(r"(?:no|without|nahi|nai|nahin).{0,20}(?:battery|backup)", text):
        return False
    if re.search(r"(?:battery|backup).{0,25}(?:chahiye|required|need|want)", text):
        return True
    return None


def _normalize_local_phone(message: str) -> str | None:
    # Conservative extraction only. Final international validation is in chat_service.
    match = re.search(r"(?<!\d)(\+\d{8,15}|03\d{9})(?!\d)", message.replace(" ", ""))
    return match.group(1) if match else None


def _extract_local_email(message: str) -> str | None:
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", message)
    return match.group(0) if match else None


def _extract_local_quotation_intent(message: str) -> bool | None:
    text = message.lower()
    if re.search(
        r"(?:no|nahi|nai|don't|do not).{0,20}(?:quotation|quote|proposal)", text
    ):
        return False
    if re.search(r"\b(?:quotation|qoutation|quote|proposal)\b", text):
        return True
    return None


def _extract_local_sales_intent(message: str) -> bool | None:
    text = message.lower()
    if any(
        x in text
        for x in ["don't contact", "do not contact", "contact nahi", "sales call nahi"]
    ):
        return False
    if _extract_local_quotation_intent(message) is True:
        return True
    if re.search(
        r"\b(order|purchase|buy|proceed)\b|contact\s+me|call\s+me|khareed", text
    ):
        return True
    return None


def _extract_local_appliances(message: str) -> list[ApplianceUsage]:
    """
    Small deterministic fallback for common appliances.
    Groq remains the primary flexible-language extractor.
    """
    text = message.lower()
    results: list[ApplianceUsage] = []

    aliases = [
        ("ac", r"\b(?:ac|air\s*conditioner)\b"),
        ("fan", r"\b(?:fan|fans)\b"),
        ("fridge", r"\b(?:fridge|refrigerator)\b"),
        ("tv", r"\b(?:tv|television)\b"),
        ("light", r"\b(?:light|lights|bulb|bulbs)\b"),
        ("washing_machine", r"\bwashing\s*machine\b"),
        ("water_pump", r"\b(?:water\s*)?pump\b"),
        ("computer", r"\b(?:computer|desktop)\b"),
        ("laptop", r"\blaptop\b"),
    ]

    for name, pattern in aliases:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        prefix = text[max(0, match.start() - 12) : match.start()]
        qty_match = re.search(r"(\d+)\s*$", prefix)
        quantity = int(qty_match.group(1)) if qty_match else 1

        capacity_ton = None
        hours = None

        if name == "ac":
            nearby = text[max(0, match.start() - 20) : min(len(text), match.end() + 30)]
            ton_match = re.search(r"(\d+(?:\.\d+)?)\s*ton", nearby)
            if ton_match:
                capacity_ton = float(ton_match.group(1))

        nearby = text[max(0, match.start() - 20) : min(len(text), match.end() + 40)]
        hour_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|ghantay|ghante)", nearby
        )
        if hour_match:
            hours = float(hour_match.group(1))

        results.append(
            ApplianceUsage(
                appliance=name,
                quantity=quantity,
                hours_per_day=hours,
                capacity_ton=capacity_ton,
            )
        )

    return results


def local_fallback_extraction(message: str) -> AgentExtraction:
    quotation = _extract_local_quotation_intent(message)
    sales = _extract_local_sales_intent(message)
    if quotation is True:
        sales = True

    return AgentExtraction(
        budget=_extract_local_budget(message),
        required_kw=_extract_local_kw(message),
        system_type=_extract_local_system_type(message),
        needs_backup=_extract_local_backup(message),
        monthly_units=_extract_local_monthly_units(message),
        appliances=_extract_local_appliances(message),
        wants_sales_contact=sales,
        wants_quotation=quotation,
        name=None,
        phone=_normalize_local_phone(message),
        email=_extract_local_email(message),
        city=None,
    )


def _clean_json_response(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def classify_customer_message(message: str) -> str:
    # Appliance/energy statements are definitely part of a sales sizing conversation.
    if (
        _extract_local_appliances(message)
        or _extract_local_monthly_units(message) is not None
        or _extract_local_kw(message) is not None
    ):
        return "sales_conversation"

    prompt = f"""
Classify this latest message for a Solar AI Sales Agent.

MESSAGE:
{message}

Return EXACTLY:
general_question
or
sales_conversation

Sizing requirements, appliance usage, monthly units, budget, quotations,
customer details and short follow-up answers are sales_conversation.
General educational solar questions are general_question.
"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Return only the requested classification.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_completion_tokens=20,
        )
        result = response.choices[0].message.content
        return (
            "general_question"
            if result and result.strip().lower() == "general_question"
            else "sales_conversation"
        )
    except Exception as error:  # noqa: BLE001
        print("MESSAGE CLASSIFICATION ERROR:", repr(error))
        return "sales_conversation"


def answer_general_question(message: str) -> str:
    prompt = f"""
You are a professional Solar AI Sales Assistant for a solar company in Pakistan.

CUSTOMER QUESTION:
{message}

{LANGUAGE_INSTRUCTIONS}

RULES:
1. Answer directly and concisely.
2. Never invent company prices, packages, discounts, stock, brands or warranties.
3. Do not claim a definite system size without evaluated requirements.
4. Never mention the underlying AI provider/model.
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional solar assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_completion_tokens=700,
    )
    reply = response.choices[0].message.content
    if not reply or not reply.strip():
        raise RuntimeError("Groq returned an empty general answer.")
    return reply.strip()


def extract_agent_data(message: str) -> AgentExtraction:
    prompt = f"""
You extract structured data from ONLY the customer's latest solar-sales message.

CUSTOMER MESSAGE:
{message}

Extract:
- budget: PKR number or null
- required_kw: explicitly requested solar kW or null
- system_type: hybrid, on-grid, off-grid, or null
- needs_backup: true/false only when explicit, otherwise null
- monthly_units: monthly electricity consumption in units/kWh, or null
- appliances: every appliance explicitly mentioned in this message
- wants_sales_contact
- wants_quotation
- name, phone, email, city

For each appliance return:
- appliance: short normalized English name, e.g. ac, fan, fridge, tv, light
- quantity: integer; default 1 only when appliance is explicitly mentioned
- wattage: only when customer gives wattage, otherwise null
- hours_per_day: only when customer gives daily hours, otherwise null
- capacity_ton: AC tonnage only when supplied, otherwise null

IMPORTANT:
- "2 fans, 1 fridge, 1.5 ton AC" is appliance data, NOT required_kw.
- "AC 6 hours daily" means AC hours_per_day=6.
- "650 units monthly" means monthly_units=650.
- Do not calculate solar kW yourself.
- Do not invent appliance wattage/hours/tonnage.
- Quotation request => wants_quotation=true and wants_sales_contact=true.
- Explicit quotation refusal => wants_quotation=false.
- Phone numbers are never budgets.
- Never invent missing information.

Return ONLY valid JSON:
{{
  "budget": null,
  "required_kw": null,
  "system_type": null,
  "needs_backup": null,
  "monthly_units": null,
  "appliances": [],
  "wants_sales_contact": null,
  "wants_quotation": null,
  "name": null,
  "phone": null,
  "email": null,
  "city": null
}}
"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract structured solar-sales data. "
                            "Return valid JSON only. Never invent missing information."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_completion_tokens=1400,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Groq returned empty extraction.")

            extracted = AgentExtraction.model_validate(
                json.loads(_clean_json_response(content))
            )

            local_quote = _extract_local_quotation_intent(message)
            if local_quote is not None:
                extracted.wants_quotation = local_quote
            if extracted.wants_quotation is True:
                extracted.wants_sales_contact = True

            local_units = _extract_local_monthly_units(message)
            if local_units is not None:
                extracted.monthly_units = local_units

            # Budget is accepted only when deterministic money context supports it.
            local_budget = _extract_local_budget(message)
            extracted.budget = local_budget

            # Keep local phone extraction conservative; chat_service validates E.164.
            if extracted.phone is not None:
                extracted.phone = _normalize_local_phone(extracted.phone)

            return extracted

        except Exception as error:  # noqa: BLE001
            print("GROQ EXTRACTION ERROR:", repr(error))
            if attempt < 2:
                time.sleep(2**attempt)
            else:
                return local_fallback_extraction(message)

    return local_fallback_extraction(message)


def generate_sales_reply(
    customer_message: str,
    requirements: ExtractedRequirements,
    recommendation: dict,
) -> str:
    prompt = f"""
You are a professional Solar AI Sales Assistant for a solar company in Pakistan.

{LANGUAGE_INSTRUCTIONS}

CUSTOMER MESSAGE:
{customer_message}

CUSTOMER REQUIREMENTS:
Budget: {requirements.budget}
Required system size: {requirements.required_kw} kW
System type: {requirements.system_type}
Battery backup: {requirements.needs_backup}
Monthly units: {requirements.monthly_units}

VERIFIED DATABASE RECOMMENDATION:
Package: {recommendation["name"]}
System size: {recommendation["system_size_kw"]} kW
System type: {recommendation["system_type"]}
Demo price: PKR {recommendation["package_price"]:,.0f}
Match score: {recommendation["match_score"]}%
Reasons: {recommendation["reasons"]}

STRICT RULES:
1. Use only verified recommendation data.
2. Never invent/modify package price or specifications.
3. Clearly treat supplied package price as demo price.
4. If system size was calculated from appliances/units, describe it as preliminary sizing.
5. Keep response concise and professional.
6. Roman Urdu uses Latin letters only.
7. Never mention the AI provider/model.
"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Explain only verified recommendation data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_completion_tokens=500,
            )
            reply = response.choices[0].message.content
            if reply and reply.strip():
                return reply.strip()
            raise RuntimeError("Groq returned empty sales reply.")
        except Exception as error:
            print("GROQ SALES REPLY ERROR:", repr(error))
            if attempt == 2:
                raise
            time.sleep(2**attempt)

    raise RuntimeError("Unable to generate sales reply.")
