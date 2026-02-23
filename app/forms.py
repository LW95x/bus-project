from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, PasswordField, DateTimeLocalField, SelectField, IntegerField, TextAreaField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from datetime import datetime
from app.models import User, Assignment, Exam, Task, Priority
from app import db
import sqlalchemy as sa

PRIORITY_CHOICES = [(p.value, p.name.capitalize()) for p in Priority]

class AssignmentForm(FlaskForm):

    def validate_due_date(self, due_date):
        if due_date.data and due_date.data < datetime.now():
            raise ValidationError("Date provided is in the past.")
        
    title = StringField('Assignment Title', validators=[DataRequired(), Length(max=256)])
    due_date = DateTimeLocalField('Due Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    priority = SelectField('Priority', coerce=int, choices=PRIORITY_CHOICES, default=Priority.MEDIUM.value)
    submit = SubmitField('Add Assignment')

class ExamForm(FlaskForm):

    def validate_exam_date(self, exam_date):
        if exam_date.data and exam_date.data < datetime.now():
            raise ValidationError("Date provided is in the past.")
        
    module = StringField('Module Name', validators=[DataRequired(), Length(max=256)])
    exam_date = DateTimeLocalField('Exam Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (Minutes)', validators=[DataRequired()])
    priority = SelectField('Priority', coerce=int, choices=PRIORITY_CHOICES, default=Priority.MEDIUM.value)
    submit = SubmitField('Add Exam')

class TaskForm(FlaskForm):

    def validate_scheduled_time(self, scheduled_time):
        if scheduled_time.data and scheduled_time.data < datetime.now():
            raise ValidationError("Date provided is in the past.")
        
    module = StringField('Module Name', validators=[DataRequired(), Length(max=256)])
    description = TextAreaField('Description', validators=[Length(max=256)])
    scheduled_time = DateTimeLocalField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (Minutes)', default=60)
    priority = SelectField('Priority', coerce=int, choices=PRIORITY_CHOICES, default=Priority.MEDIUM.value)
    
    exam_id = SelectField('Link to Exam', coerce=int, validators=[Optional()])
    assignment_id = SelectField('Link to Assignment', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Schedule Task')

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where( 
            User.username == username.data))
        if user is not None:
            raise ValidationError('This username is taken. Please provide a different username.')

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")