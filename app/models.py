from app import db, login
from flask_login import UserMixin
import sqlalchemy.orm as so
import sqlalchemy as sa
import enum
from sqlalchemy import func
from typing import Optional
import datetime

class Priority(enum.IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(nullable=False)

    # Relationship to the child entities (exams, assignments, tasks)
    exams: so.WriteOnlyMapped['Exam'] = so.relationship(back_populates='author')
    assignments: so.WriteOnlyMapped['Assignment'] = so.relationship(back_populates='author')
    tasks: so.WriteOnlyMapped['Task'] = so.relationship(back_populates='author')

class Assignment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False, nullable=False)
    due_date: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), index=True, nullable=False)
    priority: so.Mapped[Priority] = so.mapped_column(
        sa.Enum(Priority), 
        default=Priority.MEDIUM, 
        nullable=False
    )

    # Relationship to the parent entity (user)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='assignments')

    tasks: so.Mapped[list['Task']] = so.relationship(back_populates='assignment', cascade="all, delete-orphan")

class Exam(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    module: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    duration_minutes: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    exam_date: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), index=True, nullable=False)
    priority: so.Mapped[Priority] = so.mapped_column(
        sa.Enum(Priority), 
        default=Priority.MEDIUM, 
        nullable=False
    )

    # Relationship to the parent entity (user)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='exams')

    tasks: so.Mapped[list['Task']] = so.relationship(back_populates='exam', cascade="all, delete-orphan")

class Task(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    module: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(256))
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False, nullable=False)
    priority: so.Mapped[Priority] = so.mapped_column(
        sa.Enum(Priority), 
        default=Priority.MEDIUM, 
        nullable=False
    )

    # Time blocked sessions
    scheduled_time: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), index=True, nullable=False)
    duration_minutes: so.Mapped[int] = so.mapped_column(sa.Integer, default=60)

    # Relationship to the parent entity (user)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='tasks')

    # Link the task to either an Exam, or an Assignment (i.e. revision, or coursework)
    exam_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Exam.id))
    assignment_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Assignment.id))

    exam: so.Mapped[Optional['Exam']] = so.relationship(back_populates='tasks')
    assignment: so.Mapped[Optional['Assignment']] = so.relationship(back_populates='tasks')

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

