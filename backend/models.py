import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import db
from errors import StateTransitionError


class TaskStatus(enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


# Explicit state machine: each status maps to the set of valid next statuses.
# A status not present as a value means no forward transition is possible.
VALID_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.todo: frozenset({TaskStatus.in_progress}),
    TaskStatus.in_progress: frozenset({TaskStatus.done}),
    TaskStatus.done: frozenset(),
}


def _now():
    return datetime.now(timezone.utc)


class Project(db.Model):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.todo)
    priority = Column(SAEnum(TaskPriority), nullable=False, default=TaskPriority.medium)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    project = relationship("Project", back_populates="tasks")

    def transition_to(self, new_status: TaskStatus) -> None:
        """
        Apply a status transition.

        This is the single authoritative place where transition rules are enforced.
        Raises StateTransitionError if the move is not permitted by VALID_TRANSITIONS.
        Routes must never bypass this method when changing status.
        """
        allowed = VALID_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise StateTransitionError(self.status, new_status)
        self.status = new_status
        self.updated_at = _now()
