"""
AI Sales Agent Schemas
======================

Request/response models for the AI-powered solar sales agent.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentChatRequest(BaseModel):
    session_id: int | None = Field(default=None, gt=0)
    message: str = Field(min_length=1, max_length=2000)


class ApplianceUsage(BaseModel):
    appliance: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=1, ge=1, le=100)
    wattage: float | None = Field(default=None, gt=0)
    hours_per_day: float | None = Field(default=None, ge=0, le=24)
    capacity_ton: float | None = Field(default=None, gt=0, le=10)


class SolarSizingResult(BaseModel):
    estimated_peak_load_kw: float
    estimated_daily_energy_kwh: float
    recommended_system_kw: float
    estimated_battery_kwh: float | None = None
    assumptions: list[str] = Field(default_factory=list)


class ExtractedRequirements(BaseModel):
    budget: float | None = None
    required_kw: float | None = None
    system_type: str | None = None
    needs_backup: bool | None = None
    monthly_units: float | None = None
    appliances: list[ApplianceUsage] = Field(default_factory=list)


class AgentExtraction(BaseModel):
    budget: float | None = None
    required_kw: float | None = None
    system_type: str | None = None
    needs_backup: bool | None = None
    monthly_units: float | None = None
    appliances: list[ApplianceUsage] = Field(default_factory=list)

    wants_sales_contact: bool | None = None
    wants_quotation: bool | None = None

    name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    city: str | None = Field(default=None, max_length=100)


class AgentRecommendation(BaseModel):
    package_id: int
    name: str
    system_size_kw: float
    system_type: str
    package_price: float
    match_score: float
    reasons: list[str]


class AgentQuotation(BaseModel):
    proposal_id: int
    proposal_number: str
    package_id: int
    status: str
    subtotal: float
    discount: float
    total_price: float
    pdf_url: str


class AgentChatResponse(BaseModel):
    session_id: int
    customer_message: str
    extracted_requirements: AgentExtraction
    lead_id: int | None = None
    reply: str
    sizing: SolarSizingResult | None = None
    recommendations: list[AgentRecommendation] = Field(default_factory=list)
    quotation: AgentQuotation | None = None


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_message: str
    assistant_message: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: int
    messages: list[ChatMessageResponse]
