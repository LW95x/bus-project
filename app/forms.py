from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, PasswordField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import date
from app.models import User
from app import db
import sqlalchemy as sa

class AssignmentForm(FlaskForm):
    title = StringField("What is the task name", validators=[DataRequired(), Length(max=100)])
    completed = BooleanField("Completed - tick if YES")
    date_completed = DateField(
        "Expected date of completion / Date completed",
        format="%Y-%m-%d",
        default=date.today
    )
    submit = SubmitField("Submit Task")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where( 
            User.username == username.data))
        if user is not None:
            raise ValidationError('This username is taken. Please provide a different username.')

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")