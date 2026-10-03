"""Business logic for lead sales tasks."""

from datetime import datetime

from app.models.sales_task import SalesTask
from app.schemas.sales_task import SalesTaskCreate, SalesTaskUpdate
from sqlalchemy.orm import Session


def get_lead_tasks(db: Session, lead_id: int) -> list[SalesTask]:
    return (
        db.query(SalesTask)
        .filter(SalesTask.lead_id == lead_id)
        .order_by(
            SalesTask.status.asc(), SalesTask.due_at.asc(), SalesTask.created_at.desc()
        )
        .all()
    )


def get_task(db: Session, task_id: int) -> SalesTask | None:
    return db.query(SalesTask).filter(SalesTask.id == task_id).first()


def get_open_tasks(db: Session, limit: int = 100) -> list[SalesTask]:
    return (
        db.query(SalesTask)
        .filter(SalesTask.status == "pending")
        .order_by(SalesTask.due_at.asc(), SalesTask.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )


def create_task(db: Session, lead_id: int, data: SalesTaskCreate) -> SalesTask:
    task = SalesTask(lead_id=lead_id, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: SalesTask, data: SalesTaskUpdate) -> SalesTask:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(task, field, value)

    if "status" in changes:
        task.completed_at = (
            datetime.utcnow() if changes["status"] == "completed" else None
        )

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: SalesTask) -> None:
    db.delete(task)
    db.commit()
