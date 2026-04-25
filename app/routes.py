from asyncio import tasks
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, login_user, current_user, logout_user

from app import app
from app import db
from app.models import Assignment, Priority, SavedMaterial, ToDoItem, User, Task, Exam
from app.forms import AssignmentForm, RegisterForm, LoginForm, SavedMaterialForm, SubTaskForm, TaskForm, ExamForm
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
    logout_user()
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

    # CONDITONAL FORMATTING FOR ASSIGNMENTS
    today = datetime.now().date()
    for assignment in assignments:
        delta = (assignment.due_date.date() - today).days

        if assignment.completed:
            assignment.urgency = "text-muted opacity-50"
            assignment.text_style = "text-decoration-line-through"

        elif delta < 0:
            assignment.urgency = "table-secondary"
            assignment.text_style = ""
        elif delta <= 7:
            assignment.urgency = "table-danger"
            assignment.text_style = ""
        elif delta <= 14:
            assignment.urgency = "table-warning"
            assignment.text_style = ""
        else:
            assignment.urgency = "table-info"
            assignment.text_style = ""

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

    # CONDITONAL FORMATTING FOR EXAMS
    today = datetime.now().date()
    for exam in exams:
        delta = (exam.exam_date.date() - today).days

        if delta < 0:
            exam.urgency = "table-secondary"
        elif delta <= 7:
            exam.urgency = "table-danger"
        elif delta <= 14:
            exam.urgency = "table-warning"
        else:
            exam.urgency = "table-info"

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

    # CONDITONAL FORMATTING FOR TASKS

    today = datetime.now().date()

    for task in tasks:
        delta = (task.scheduled_time.date() - today).days

        if task.completed:
            task.row_class = "text-muted opacity-50"
            task.text_style = "text-decoration-line-through"
        
        elif delta < 0:
            task.row_class = "table-danger fw-bold"
            task.text_style = ""
        elif delta <= 7:
            task.row_class = "table-danger"
            task.text_style = ""
        elif delta <= 14:
            task.row_class = "table-warning"
            task.text_style = ""
        else:
            task.row_class = "table-info"
            task.text_style = ""

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
    if item_type == 'assignment':
        item = db.session.get(Assignment, item_id)

        if item and item.author == current_user:
            item.completed = not item.completed
            db.session.commit()

    elif item_type == 'task':
        item = db.session.get(Task, item_id)

        if item and item.author == current_user:
            item.completed = not item.completed
            db.session.commit()

    elif item_type == 'todo':
        item = db.session.get(ToDoItem, item_id)

        if item:
            if item.exam and item.exam.author == current_user:
                item.completed = not item.completed
                db.session.commit()

            elif item.assignment and item.assignment.author == current_user:
                item.completed = not item.completed
                db.session.commit()

    return redirect(request.referrer or url_for('index'))

@app.route('/exam/<int:id>')
@login_required
def view_exam(id):
    exam = Exam.query.get_or_404(id)
    material_form = SavedMaterialForm() 
    subtask_form = SubTaskForm() 

    if exam.author != current_user:
        flash("You are not the owner of this exam.")
        return redirect(url_for('index'))

    tasks = exam.todo_items

    for task in tasks:
        if task.completed:
            task.row_class = "text-muted opacity-50"
            task.text_style = "text-decoration-line-through"
        else:
            task.row_class = ""
            task.text_style = ""
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.completed)

    percentage = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    return render_template('view-exam.html', exam=exam, material_form=material_form, subtask_form=subtask_form, tasks=tasks, total_tasks=total_tasks, completed_count=completed_tasks, percentage=percentage)

@app.route('/assignment/<int:id>')
@login_required
def view_assignment(id):
    assignment = Assignment.query.get_or_404(id)

    if assignment.author != current_user:
        flash("You are not the owner of this assignment.")
        return redirect(url_for('index'))

    material_form = SavedMaterialForm()
    subtask_form = SubTaskForm()

    tasks = assignment.todo_items

    for task in tasks:
        if task.completed:
            task.row_class = "text-muted opacity-50"
            task.text_style = "text-decoration-line-through"
        else:
            task.row_class = ""
            task.text_style = ""

    total_tasks = len(tasks)
    completed_count = sum(1 for task in tasks if task.completed)
    percentage = round((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    return render_template(
        'view-assignment.html',
        assignment=assignment,
        material_form=material_form,
        subtask_form=subtask_form,
        tasks=tasks,
        total_tasks=total_tasks,
        completed_count=completed_count,
        percentage=percentage
    )

@app.route("/exams/<int:exam_id>/notes", methods=["POST"])
@login_required
def save_exam_notes(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if exam.author != current_user:
        flash("You are not the owner of this exam.")
        return redirect(url_for('index'))

    notes = request.form.get("notes")
    exam.notes = notes
    db.session.commit()
    flash("Exam notes saved successfully.")
    return redirect(url_for('view_exam', id=exam_id))

@app.route("/assignments/<int:assignment_id>/notes", methods=["POST"])
@login_required
def save_assignment_notes(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if assignment.author != current_user:
        flash("You are not the owner of this assignment.")
        return redirect(url_for('index'))

    notes = request.form.get("notes")
    assignment.notes = notes
    db.session.commit()
    flash("Assignment notes saved successfully.")
    return redirect(url_for('view_assignment', id=assignment_id))

@app.route("/exams/<int:exam_id>/materials/add", methods=["POST"])
@login_required
def add_exam_material(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if exam.author != current_user:
        flash("You are not the owner of this exam.")
        return redirect(url_for("index"))

    title = request.form.get("title")
    url = request.form.get("url")

    material = SavedMaterial(
        title=title,
        url=url,
        exam_id=exam.id
    )

    db.session.add(material)
    db.session.commit()

    flash("Saved material added.")
    return redirect(url_for("view_exam", id=exam.id))

@app.route("/assignments/<int:assignment_id>/materials/add", methods=["POST"])
@login_required
def add_assignment_material(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if assignment.author != current_user:
        flash("You are not the owner of this assignment.")
        return redirect(url_for("index"))

    title = request.form.get("title")
    url = request.form.get("url")

    material = SavedMaterial(
        title=title,
        url=url,
        assignment_id=assignment.id
    )

    db.session.add(material)
    db.session.commit()

    flash("Saved material added.")
    return redirect(url_for("view_assignment", id=assignment.id))

@app.route("/exams/<int:exam_id>/subtasks/add", methods=["POST"])
@login_required
def add_exam_subtask(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if exam.author != current_user:
        flash("You are not the owner of this exam.")
        return redirect(url_for("index"))

    description = request.form.get("description")
    priority = request.form.get("priority")

    subtask = ToDoItem(
        description=description,
        priority=Priority(int(priority)),
        exam_id=exam.id
    )

    db.session.add(subtask)
    db.session.commit()

    flash("Sub-task added.")
    return redirect(url_for("view_exam", id=exam.id))

@app.route("/assignments/<int:assignment_id>/subtasks/add", methods=["POST"])
@login_required
def add_assignment_subtask(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if assignment.author != current_user:
        flash("You are not the owner of this assignment.")
        return redirect(url_for("index"))

    description = request.form.get("description")
    priority = request.form.get("priority")

    subtask = ToDoItem(
        description=description,
        priority=Priority(int(priority)),
        assignment_id=assignment.id
    )

    db.session.add(subtask)
    db.session.commit()

    flash("Sub-task added.")
    return redirect(url_for("view_assignment", id=assignment.id))

@app.route("/todo-items/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo_item(todo_id):
    todo = ToDoItem.query.get_or_404(todo_id)

    if todo.exam and todo.exam.author != current_user:
        flash("You are not the owner of this exam.")
        return redirect(url_for("index"))

    if todo.assignment and todo.assignment.author != current_user:
        flash("You are not the owner of this assignment.")
        return redirect(url_for("index"))

    if todo.exam:
        redirect_url = url_for("view_exam", id=todo.exam.id)
    else:
        redirect_url = url_for("view_assignment", id=todo.assignment.id)

    db.session.delete(todo)
    db.session.commit()

    flash("Sub-task deleted.")
    return redirect(redirect_url)

@app.route("/materials/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_saved_material(material_id):
    material = SavedMaterial.query.get_or_404(material_id)

    if material.exam:
        if material.exam.author != current_user:
            flash("You are not the owner of this exam.")
            return redirect(url_for("index"))

        redirect_url = url_for("view_exam", id=material.exam.id)

    elif material.assignment:
        if material.assignment.author != current_user:
            flash("You are not the owner of this assignment.")
            return redirect(url_for("index"))

        redirect_url = url_for("view_assignment", id=material.assignment.id)

    else:
        flash("Saved material has no parent.")
        return redirect(url_for("index"))

    db.session.delete(material)
    db.session.commit()

    flash("Saved material deleted.")
    return redirect(redirect_url)