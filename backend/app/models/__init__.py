"""
Database Models
===============

Exports all SQLAlchemy models so they can be discovered by Alembic
and imported consistently throughout the application.
"""

from app.models.battery import Battery
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.inverter import Inverter
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.lead_note import LeadNote
from app.models.package_item import PackageItem
from app.models.product import Product
from app.models.proposal import Proposal
from app.models.proposal_item import ProposalItem
from app.models.sales_task import SalesTask
from app.models.solar_package import SolarPackage
from app.models.solar_panel import SolarPanel
from app.models.user import User

__all__ = [
    "Battery",
    "ChatMessage",
    "ChatSession",
    "Inverter",
    "Lead",
    "LeadActivity",
    "LeadNote",
    "PackageItem",
    "Product",
    "Proposal",
    "ProposalItem",
    "SalesTask",
    "SolarPackage",
    "SolarPanel",
    "User",
]
