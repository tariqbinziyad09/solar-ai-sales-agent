"""
Chat Message Model
==================

Stores individual user and assistant messages
belonging to a chat session.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # The conversation this message belongs to.
    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Customer's original message.
    customer_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Agent's response to that message.
    assistant_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )
