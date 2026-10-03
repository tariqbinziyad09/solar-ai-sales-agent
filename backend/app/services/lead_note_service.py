"""Business logic for CRM lead notes."""

from app.models.lead_note import LeadNote
from sqlalchemy.orm import Session


def get_lead_notes(db: Session, lead_id: int) -> list[LeadNote]:
    return (
        db.query(LeadNote)
        .filter(LeadNote.lead_id == lead_id)
        .order_by(LeadNote.created_at.desc(), LeadNote.id.desc())
        .all()
    )


def get_lead_note(db: Session, note_id: int) -> LeadNote | None:
    return db.get(LeadNote, note_id)


def create_lead_note(
    db: Session, lead_id: int, author_user_id: int, content: str
) -> LeadNote:
    clean_content = content.strip()
    if not clean_content:
        raise ValueError("Note content cannot be empty.")
    note = LeadNote(
        lead_id=lead_id, author_user_id=author_user_id, content=clean_content
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_lead_note(db: Session, note: LeadNote, content: str) -> LeadNote:
    clean_content = content.strip()
    if not clean_content:
        raise ValueError("Note content cannot be empty.")
    note.content = clean_content
    db.commit()
    db.refresh(note)
    return note


def delete_lead_note(db: Session, note: LeadNote) -> None:
    db.delete(note)
    db.commit()
