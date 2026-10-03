from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Lead(Base):
    """Represents a potential solar customer."""

    __tablename__ = "leads"

    chat_sessions = relationship("ChatSession", back_populates="lead")
    activities = relationship(
        "LeadActivity", back_populates="lead", cascade="all, delete-orphan"
    )

    proposals = relationship("Proposal", back_populates="lead")

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    monthly_bill: Mapped[float | None] = mapped_column(Float, nullable=True)
    interested_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="website", nullable=False)

    qualification_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qualification_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Staff member currently responsible for this lead.
    #
    # NULL means the lead has not been assigned yet.
    # Customer-facing AI can therefore create a lead first,
    # and Admin/Manager can assign it later.
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
    )
    # Sales follow-up state.
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    follow_up_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    follow_up_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
