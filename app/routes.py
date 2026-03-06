from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, login_user, current_user

from app import app
from app import db
from app.models import Assignment, Priority, User, Task, Exam
from app.forms import AssignmentForm, RegisterForm, LoginForm, TaskForm, ExamForm
import sqlalchemy as sa
# romeo test 260302

@app.route('/')
@login_required
def index():
    return render_template("index.html")

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

        flash("User registration was successful.")
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("User login was successful.")
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("User logout was successful.")
    return redirect(url_for('login'))

@app.route('/add-assignment', methods=['GET', 'POST'])
@login_required
def add_assignment():
    form = AssignmentForm()

    if form.validate_on_submit():
        assignment = Assignment(
            title=form.title.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            author=current_user
        )
        db.session.add(assignment)
        db.session.commit()
        flash("The assignment was successfully added.")
        return redirect(url_for('view_assignments'))

    return render_template("add-assignment.html", form=form)

@app.route('/view-assignments', methods=['GET', 'POST'])
@login_required
def view_assignments():

    sort_type = request.args.get('type', 'soonest')
    priority_type = request.args.get('priority', '')

    query = Assignment.query.filter_by(author=current_user)

    if priority_type:
        target_priority = Priority(int(priority_type))
        query = query.filter(Assignment.priority == target_priority)

    if sort_type == 'descending':
        query = query.order_by(Assignment.due_date.desc())
    else:
        query = query.order_by(Assignment.due_date.asc())


    assignments = query.all()

    return render_template('view-assignments.html', assignments=assignments, type=sort_type, priority=priority_type)

@app.route('/add-exam', methods=['GET', 'POST'])
@login_required
def add_exam():
    form = ExamForm()

    if form.validate_on_submit():
        exam = Exam(
            module=form.module.data,             
            exam_date=form.exam_date.data,       
            duration_minutes=form.duration_minutes.data, 
            priority=form.priority.data,         
            author=current_user
        )
        db.session.add(exam)
        db.session.commit()
        flash("The exam was successfully added.")
        return redirect(url_for('view_exams'))

    return render_template("add-exam.html", form=form)

@app.route('/view-exams', methods=['GET', 'POST'])
@login_required
def view_exams():
    sort_type = request.args.get('type', '')
    priority_type = request.args.get('priority', '')

    query = Exam.query.filter_by(author=current_user)

    if priority_type:
        target_priority = Priority(int(priority_type))
        query = query.filter(Exam.priority == target_priority)

    if sort_type == 'descending':
        query = query.order_by(Exam.exam_date.desc())
    else:
        query = query.order_by(Exam.exam_date.asc())

    exams = query.all()

    return render_template('view-exams.html', exams=exams, type=sort_type, priority=priority_type)

@app.route('/add-task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()

    # Populate dropdowns with the existing user's exams and assignments
    form.exam_id.choices = [(0, 'None')] + [
    (e.id, e.module) for e in db.session.scalars(current_user.exams.select()).all()
    ]
    form.assignment_id.choices = [(0, 'None')] + [
    (a.id, a.title) for a in db.session.scalars(current_user.assignments.select()).all()
    ]

    if form.validate_on_submit():

        # The form will populate with either an exam task or assignment task
        eid = form.exam_id.data if form.exam_id.data != 0 else None
        aid = form.assignment_id.data if form.assignment_id.data != 0 else None

        task = Task(
            module=form.module.data,
            description=form.description.data,
            priority=form.priority.data,
            scheduled_time=form.scheduled_time.data, 
            duration_minutes=form.duration_minutes.data,
            exam_id=eid,
            assignment_id=aid,
            author=current_user
        )
        db.session.add(task)
        db.session.commit()
        flash("The task was successfully added.")
        return redirect(url_for('view_tasks'))

    return render_template("add-task.html", form=form)

@app.route('/view-tasks', methods=['GET', 'POST'])
@login_required
def view_tasks():
    sort_type = request.args.get('type', '')
    priority_type = request.args.get('priority', '')
    exam_filter = request.args.get('exam_id', '')
    assign_filter = request.args.get('assignment_id', '')

    query = Task.query.filter_by(author=current_user)

    if exam_filter:
        query = query.filter(Task.exam_id == int(exam_filter))
    if assign_filter:
        query = query.filter(Task.assignment_id == int(assign_filter))

    if priority_type:
        target_priority = Priority(int(priority_type))
        query = query.filter(Task.priority == target_priority)

    if sort_type == 'descending':
        query = query.order_by(Task.scheduled_time.desc())
    else:
        query = query.order_by(Task.scheduled_time.asc())

    tasks = query.all()

    user_exams = Exam.query.filter_by(author=current_user).all()
    user_assigns = Assignment.query.filter_by(author=current_user).all()

    return render_template('view-tasks.html', tasks=tasks, type=sort_type, priority=priority_type, user_exams=user_exams, user_assigns=user_assigns, selected_exam=exam_filter, selected_assign=assign_filter)

@app.route('/update-assignment/<int:assignment_id>', methods=['GET','POST'])
@login_required
def updating_assignment(assignment_id):

    assignment_to_update = Assignment.query.get_or_404(assignment_id)

    form = AssignmentForm(obj=assignment_to_update)
    form.submit.label.text = "Update Assignment"

    if form.validate_on_submit():
        form.populate_obj(assignment_to_update)
        db.session.commit()
        flash("The assignment was successfully updated.")
        return redirect(url_for('view_assignments'))

    return render_template("update-assignment.html", form=form)

@app.route('/update-exam/<int:exam_id>', methods=['GET','POST'])
@login_required
def updating_exam(exam_id):

    exam_to_update = Exam.query.get_or_404(exam_id)

    form = ExamForm(obj=exam_to_update)
    form.submit.label.text = "Update Exam"

    if form.validate_on_submit():
        form.populate_obj(exam_to_update)
        db.session.commit()
        flash("The exam was successfully updated.")
        return redirect(url_for('view_exams'))

    return render_template("update-exam.html", form=form)

@app.route('/update-task/<int:task_id>', methods=['GET','POST'])
@login_required
def updating_task(task_id):

    task_to_update = Task.query.get_or_404(task_id)

    form = TaskForm(obj=task_to_update)
    form.submit.label.text = "Update Task"

    # Populate dropdowns with the existing user's exams and assignments
    form.exam_id.choices = [(0, 'None')] + [(e.id, e.module) for e in db.session.scalars(current_user.exams.select()).all()]
    form.assignment_id.choices = [(0, 'None')] + [(a.id, a.title) for a in db.session.scalars(current_user.assignments.select()).all()]

    if form.validate_on_submit():
        form.populate_obj(task_to_update)

        if task_to_update.exam_id == 0: task_to_update.exam_id = None
        if task_to_update.assignment_id == 0: task_to_update.assignment_id = None

        db.session.commit()
        flash("The task was successfully updated.")
        return redirect(url_for('view_tasks'))

    return render_template("update-task.html", form=form)

@app.route('/delete-assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    assignment_to_delete = Assignment.query.get_or_404(assignment_id)

    if assignment_to_delete.author == current_user:
        try:
            db.session.delete(assignment_to_delete)
            db.session.commit()
            flash("The assignment was successfully deleted.")
        except:
            db.session.rollback()
            flash("An error occurred while deleting the assignment.")
    else:
        flash("You are not the owner of this assignment.")
    
    return redirect(url_for('view_assignments'))

@app.route('/delete-exam/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam_to_delete = Exam.query.get_or_404(exam_id)

    if exam_to_delete.author == current_user:
        try:
            db.session.delete(exam_to_delete)
            db.session.commit()
            flash("The exam was successfully deleted.")
        except:
            db.session.rollback()
            flash("An error occurred while deleting the exam.")
    else:
        flash("You are not the owner of this exam.")

    return redirect(url_for('view_exams'))

@app.route('/delete-task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task_to_delete = Task.query.get_or_404(task_id)

    if task_to_delete.author == current_user:
        try:
            db.session.delete(task_to_delete)
            db.session.commit()
            flash("The task was successfully deleted.")
        except:
            db.session.rollback()
            flash("An error occurred while deleting the task.")
    else:
        flash("You are not the owner of this task.")

    return redirect(url_for('view_tasks'))

@app.route('/toggle-<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def toggle_status(item_type, item_id):
    model = Assignment if item_type == 'assignment' else Task

    item = db.session.get(model, item_id)
    
    if item and item.author == current_user:
        item.completed = not item.completed
        db.session.commit()
   
    return redirect(request.referrer or url_for('index'))