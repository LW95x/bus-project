from app import db, login
from flask_login import UserMixin
import sqlalchemy.orm as so
import sqlalchemy as sa

from datetime import datetime, timezone

class Assignment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False, nullable=False)
    date_completed: so.Mapped[str] = so.mapped_column(sa.DATE, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Task {self.id}, {self.title}, {self.completed}, {self.date_completed}>'

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(nullable=False)

    def __repr__(self):
        return f'<Login {self.id}, {self.username}>'
    

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))