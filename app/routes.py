from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, session
from flask_login import login_required, login_user

from app import app
from app import db
from app.models import Assignment, User
from app.forms import AssignmentForm, RegisterForm, LoginForm


@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/add-assignment', methods=['GET', 'POST'])
@login_required
def add_assignment():
    form = AssignmentForm()

    if form.validate_on_submit():
        assignment = Assignment(
            title=form.title.data,
            completed=form.completed.data,
            date_completed=form.date_completed.data
        )
        db.session.add(assignment)
        db.session.commit()
        flash("The assignment was successfully added.")
        return redirect(url_for('index'))

    return render_template("add-assignment.html", form=form)

@app.route('/view_assignments', methods=['GET', 'POST'])
def view_assignments():
    assignments = Assignment.query.all()

    return render_template('view-assignments.html', assignments=assignments)

@app.route('/updating/<int:task_id>', methods=['GET','POST'])
def updating_task(task_id):

    task_to_update = Assignment.query.get_or_404(task_id)

    form = AssignmentForm(obj=task_to_update)

    if form.validate_on_submit():
        form.populate_obj(task_to_update)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template("updating.html", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)

        user = User(
            username = form.username.data,
            password_hash = hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))