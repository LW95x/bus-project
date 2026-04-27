import os
os.environ['DATABASE_URI'] = 'sqlite:///test.db'

from datetime import datetime, timedelta
import pytest

from app import app, db
from app.models import Assignment, Task, ToDoItem

# ---------------------------------------------------------------
# Test setup
# ---------------------------------------------------------------
# The two "fixtures" defined below are reusable functions that PyTest
# automatically runs before each test. They make sure that every test
# starts in a fresh state:
#
#   1. A separate test database is used (instance/test.db) so the
#      real app.db is never touched. Empty tables are created at
#      the start of each test and wiped at the end.
#   2. A fake "browser" (Flask's built-in test client) is provided
#      so tests can visit pages and submit forms without us having
#      to start the real web server.
#   3. A single test user is registered and logged in, because most
#      pages in Stacked Deck require an authenticated user.
#
# How to run the tests:
#   1. Open a terminal in the project root (the folder containing
#      the app/ folder).
#   2. Activate the virtual environment:
#        source .venv/bin/activate     (Linux / macOS)
#        .venv\Scripts\activate        (Windows)
#   3. Run:
#        pytest tests/app_test.py -v
# ---------------------------------------------------------------

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def logged_in_client(client):
    client.post('/register', data={
        'username': 'tester',
        'password': 'pw',
        'confirm_password': 'pw',
    }, follow_redirects=True)
    return client


def _future(days):
    """Return a datetime-local string `days` days in the future."""
    return (datetime.now() + timedelta(days=days)).replace(
        hour=10, minute=0, second=0, microsecond=0
    ).strftime('%Y-%m-%dT%H:%M')


# ---------------------------------------------------------------
# Story: S1 - Create assignment card
# Acceptance Criteria:
#   GIVEN I enter a title, due date and priority
#   WHEN I click "Save"
#   THEN a new assignment card appears on my dashboard
#   GIVEN required fields are empty
#   WHEN I click "Save"
#   THEN an error message is displayed
# ---------------------------------------------------------------
def test_s1_create_assignment_card(logged_in_client):
    # Happy path
    resp = logged_in_client.post('/add-assignment', data={
        'title': 'Coursework Essay',
        'due_date': _future(7),
        'priority': 2,
    })
    assert resp.status_code == 302
    dashboard = logged_in_client.get('/view-assignments')
    assert b'Coursework Essay' in dashboard.data

    # Error path: empty title -> form re-rendered, nothing saved
    before_count = Assignment.query.count()
    resp = logged_in_client.post('/add-assignment', data={
        'title': '',
        'due_date': _future(7),
        'priority': 2,
    })
    assert resp.status_code == 200
    assert Assignment.query.count() == before_count


# ---------------------------------------------------------------
# Story: S2 - View assignment cards
# Acceptance Criteria:
#   GIVEN at least one saved assignment
#   WHEN I open the dashboard
#   THEN all cards are displayed with title and due date visible
#   GIVEN no saved assignments
#   WHEN I open the dashboard
#   THEN the option to create a new assignment is shown
# ---------------------------------------------------------------
def test_s2_view_assignment_cards(logged_in_client):
    # Empty state: option to add a new assignment is shown
    resp = logged_in_client.get('/view-assignments')
    assert b'Add New Assignment' in resp.data

    # With one assignment: title is visible on the dashboard
    logged_in_client.post('/add-assignment', data={
        'title': 'My Essay',
        'due_date': _future(5),
        'priority': 2,
    })
    resp = logged_in_client.get('/view-assignments')
    assert b'My Essay' in resp.data


# ---------------------------------------------------------------
# Story: S3 - Sort assignments by due date
# Acceptance Criteria:
#   GIVEN multiple assignments exist
#   WHEN they are displayed
#   THEN they are shown in chronological order by due date,
#        with a dropdown to switch between ascending and descending
# ---------------------------------------------------------------
def test_s3_sort_assignments_by_due_date(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Alpha', 'due_date': _future(1), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Beta', 'due_date': _future(5), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Gamma', 'due_date': _future(10), 'priority': 2,
    })

    asc = logged_in_client.get('/view-assignments?type=ascending').data
    assert asc.index(b'Alpha') < asc.index(b'Beta') < asc.index(b'Gamma')

    desc = logged_in_client.get('/view-assignments?type=descending').data
    assert desc.index(b'Gamma') < desc.index(b'Beta') < desc.index(b'Alpha')


# ---------------------------------------------------------------
# Story: S4 - Deadline urgency colour change
# Acceptance Criteria:
#   GIVEN an assignment with an upcoming deadline
#   WHEN the deadline approaches
#   THEN a visual colour distinction is shown
#   (Tiers: red < 1 week, yellow 1-2 weeks, blue 2+ weeks)
# ---------------------------------------------------------------
def test_s4_deadline_urgency_colour_change(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Soon', 'due_date': _future(3), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Mid', 'due_date': _future(10), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Far', 'due_date': _future(30), 'priority': 2,
    })

    page = logged_in_client.get('/view-assignments').data
    assert b'table-danger' in page    # red, < 1 week
    assert b'table-warning' in page   # yellow, 1-2 weeks
    assert b'table-info' in page      # blue, 2+ weeks


# ---------------------------------------------------------------
# Story: S5 - Edit existing assignment
# Acceptance Criteria:
#   GIVEN an existing assignment
#   WHEN I update its details
#   THEN my modifications can be made and saved
# ---------------------------------------------------------------
def test_s5_edit_existing_assignment(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Old Title', 'due_date': _future(7), 'priority': 2,
    })
    a = Assignment.query.first()

    logged_in_client.post(f'/update-assignment/{a.id}', data={
        'title': 'New Title', 'due_date': _future(7), 'priority': 2,
    })

    page = logged_in_client.get('/view-assignments').data
    assert b'New Title' in page


# ---------------------------------------------------------------
# Story: S6 - Delete existing assignment
# Acceptance Criteria:
#   GIVEN an existing assignment card
#   WHEN I click delete
#   THEN the card is deleted and no longer appears
# ---------------------------------------------------------------
def test_s6_delete_existing_assignment(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'To Delete', 'due_date': _future(7), 'priority': 2,
    })
    a = Assignment.query.first()

    logged_in_client.post(f'/delete-assignment/{a.id}')

    page = logged_in_client.get('/view-assignments').data
    assert b'To Delete' not in page


# ---------------------------------------------------------------
# Story: S7 - Colourblind-friendly palette
# Acceptance Criteria:
#   GIVEN I am a colourblind student
#   WHEN I view my assignments
#   THEN the colours used to indicate urgency are distinguishable (e.g. red / yellow / blue)
# ---------------------------------------------------------------
def test_s7_colourblind_friendly_palette(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Soon', 'due_date': _future(3), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Mid', 'due_date': _future(10), 'priority': 2,
    })
    logged_in_client.post('/add-assignment', data={
        'title': 'Far', 'due_date': _future(30), 'priority': 2,
    })

    page = logged_in_client.get('/view-assignments').data
    # Tiers use red / yellow / blue (not red / green)
    assert b'table-danger' in page
    assert b'table-warning' in page
    assert b'table-info' in page
    assert b'table-success' not in page


# ---------------------------------------------------------------
# Story: S8 - Organise by module
# Acceptance Criteria:
#   GIVEN I am scheduling a task
#   WHEN I input its details
#   THEN I can specify a module
#   THEN tasks can be viewed and filtered by their linked assignment
# ---------------------------------------------------------------
def test_s8_organise_by_module(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Coursework', 'due_date': _future(14), 'priority': 2,
    })
    a = Assignment.query.first()

    logged_in_client.post('/add-task', data={
        'module': 'CS101',
        'description': 'Read chapter 1',
        'scheduled_time': _future(2),
        'duration_minutes': 60,
        'priority': 2,
        'exam_id': 0,
        'assignment_id': a.id,
    })

    page = logged_in_client.get(f'/view-tasks?assignment_id={a.id}').data
    assert b'CS101' in page


# ---------------------------------------------------------------
# Story: S9 - Attach library lists / references
# Acceptance Criteria:
#   GIVEN an existing assignment card
#   WHEN I navigate to the references section
#   THEN I can add a hyperlink/text reference
#   GIVEN a reference has been added
#   WHEN I view the card
#   THEN the reference is visible
# ---------------------------------------------------------------
def test_s9_attach_references(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Essay', 'due_date': _future(14), 'priority': 2,
    })
    a = Assignment.query.first()

    logged_in_client.post(f'/assignments/{a.id}/materials/add', data={
        'title': 'Reading List',
        'url': 'https://library.example.com/list',
    })

    page = logged_in_client.get(f'/assignment/{a.id}').data
    assert b'Reading List' in page
    assert b'https://library.example.com/list' in page


# ---------------------------------------------------------------
# Story: S10 - Attach study session
# Acceptance Criteria:
#   GIVEN an existing assignment
#   WHEN I schedule a study session (a Task linked to the assignment)
#   THEN a planned date and time can be entered and saved
#   GIVEN a saved study session
#   WHEN I view the assignment's tasks
#   THEN it is displayed
#   GIVEN a saved study session
#   WHEN I edit it
#   THEN it can be updated or removed
# ---------------------------------------------------------------
def test_s10_attach_study_session(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Essay', 'due_date': _future(14), 'priority': 2,
    })
    a = Assignment.query.first()

    # Create study session
    logged_in_client.post('/add-task', data={
        'module': 'CS101',
        'description': 'Library session',
        'scheduled_time': _future(2),
        'duration_minutes': 90,
        'priority': 2,
        'exam_id': 0,
        'assignment_id': a.id,
    })
    page = logged_in_client.get(f'/view-tasks?assignment_id={a.id}').data
    assert b'Library session' in page

    # Update + delete the study session
    t = Task.query.first()
    logged_in_client.post(f'/update-task/{t.id}', data={
        'module': 'CS101',
        'description': 'Library session',
        'scheduled_time': _future(5),
        'duration_minutes': 90,
        'priority': 2,
        'exam_id': 0,
        'assignment_id': a.id,
    })
    logged_in_client.post(f'/delete-task/{t.id}')
    page = logged_in_client.get(f'/view-tasks?assignment_id={a.id}').data
    assert b'Library session' not in page


# ---------------------------------------------------------------
# Story: S12 - Add notes / to-do list
# Acceptance Criteria:
#   GIVEN an existing card
#   WHEN I navigate to the notes section
#   THEN I can type and save a free-text note
#   GIVEN a saved note
#   WHEN I reopen the card
#   THEN the note is still visible and editable
#   GIVEN an existing to-do item
#   WHEN I click delete
#   THEN the to-do is removed
# ---------------------------------------------------------------
def test_s12_add_notes_and_todos(logged_in_client):
    logged_in_client.post('/add-assignment', data={
        'title': 'Essay', 'due_date': _future(14), 'priority': 2,
    })
    a = Assignment.query.first()

    # Save and reload a note
    logged_in_client.post(f'/assignments/{a.id}/notes', data={
        'notes': 'Remember to cite sources',
    })
    page = logged_in_client.get(f'/assignment/{a.id}').data
    assert b'Remember to cite sources' in page

    # Add a to-do, reload, see it
    logged_in_client.post(f'/assignments/{a.id}/subtasks/add', data={
        'description': 'Read chapter 2',
        'priority': 2,
    })
    todo = ToDoItem.query.first()
    page = logged_in_client.get(f'/assignment/{a.id}').data
    assert b'Read chapter 2' in page

    # Delete the to-do, reload, gone
    logged_in_client.post(f'/todo-items/{todo.id}/delete')
    page = logged_in_client.get(f'/assignment/{a.id}').data
    assert b'Read chapter 2' not in page
