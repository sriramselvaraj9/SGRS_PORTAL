"""
Student Grievance Redressal System
A Flask-based web application for managing student grievances.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grievances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────── Models ───────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, authority, admin
    department = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'


class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # academic, administrative, hostel, examination
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(30), default='submitted')  # submitted, in_review, in_progress, escalated, resolved, closed
    is_anonymous = db.Column(db.Boolean, default=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    escalation_level = db.Column(db.Integer, default=0)

    student = db.relationship('User', foreign_keys=[student_id], backref='grievances_filed')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='grievances_assigned')
    updates = db.relationship('GrievanceUpdate', backref='grievance', lazy=True, order_by='GrievanceUpdate.created_at.desc()')
    feedback = db.relationship('Feedback', backref='grievance', uselist=False)

    def __repr__(self):
        return f'<Grievance {self.ticket_id}>'


class GrievanceUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievance.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status_change = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='updates_made')


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievance.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────── Helper Functions ─────────────────────

def generate_ticket_id():
    """Generate a unique ticket ID like GRV-20260219-0001."""
    today = datetime.utcnow().strftime('%Y%m%d')
    last = Grievance.query.filter(Grievance.ticket_id.like(f'GRV-{today}-%')).order_by(Grievance.id.desc()).first()
    if last:
        num = int(last.ticket_id.split('-')[-1]) + 1
    else:
        num = 1
    return f'GRV-{today}-{num:04d}'


def get_deadline(priority):
    """Return resolution deadline based on priority."""
    days_map = {'low': 14, 'medium': 7, 'high': 3, 'urgent': 1}
    return datetime.utcnow() + timedelta(days=days_map.get(priority, 7))


def auto_assign(category):
    """Auto-assign grievance to an authority handling the category/department."""
    authority = User.query.filter_by(role='authority', department=category).first()
    if not authority:
        authority = User.query.filter_by(role='admin').first()
    return authority.id if authority else None


def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator to require specific roles."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────── Routes ───────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ── Authentication ──

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'student')
        department = request.form.get('department', '')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role,
            department=department if role == 'authority' else None
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Dashboard ──

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])

    if user.role == 'student':
        grievances = Grievance.query.filter_by(student_id=user.id).order_by(Grievance.created_at.desc()).all()
        stats = {
            'total': len(grievances),
            'pending': len([g for g in grievances if g.status in ('submitted', 'in_review', 'in_progress')]),
            'resolved': len([g for g in grievances if g.status in ('resolved', 'closed')]),
            'escalated': len([g for g in grievances if g.status == 'escalated']),
        }
    elif user.role == 'authority':
        grievances = Grievance.query.filter_by(assigned_to=user.id).order_by(Grievance.created_at.desc()).all()
        stats = {
            'total': len(grievances),
            'pending': len([g for g in grievances if g.status in ('submitted', 'in_review', 'in_progress')]),
            'resolved': len([g for g in grievances if g.status in ('resolved', 'closed')]),
            'escalated': len([g for g in grievances if g.status == 'escalated']),
        }
    else:  # admin
        grievances = Grievance.query.order_by(Grievance.created_at.desc()).all()
        stats = {
            'total': len(grievances),
            'pending': len([g for g in grievances if g.status in ('submitted', 'in_review', 'in_progress')]),
            'resolved': len([g for g in grievances if g.status in ('resolved', 'closed')]),
            'escalated': len([g for g in grievances if g.status == 'escalated']),
        }

    # Overdue grievances
    now = datetime.utcnow()
    overdue = [g for g in grievances if g.deadline and g.deadline < now and g.status not in ('resolved', 'closed')]
    stats['overdue'] = len(overdue)

    return render_template('dashboard.html', user=user, grievances=grievances, stats=stats)


# ── Grievance Submission ──

@app.route('/grievance/new', methods=['GET', 'POST'])
def submit_grievance():
    if request.method == 'POST':
        is_anonymous = 'is_anonymous' in request.form
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        category = request.form['category']
        priority = request.form.get('priority', 'medium')

        student_id = session.get('user_id') if not is_anonymous else None

        grievance = Grievance(
            ticket_id=generate_ticket_id(),
            title=title,
            description=description,
            category=category,
            priority=priority,
            is_anonymous=is_anonymous,
            student_id=student_id,
            assigned_to=auto_assign(category),
            deadline=get_deadline(priority),
        )
        db.session.add(grievance)
        db.session.commit()

        # Add initial update
        update = GrievanceUpdate(
            grievance_id=grievance.id,
            message='Grievance submitted successfully and routed to the concerned authority.',
            status_change='submitted'
        )
        db.session.add(update)
        db.session.commit()

        flash(f'Grievance submitted! Your ticket ID is {grievance.ticket_id}. Save it for tracking.', 'success')
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('track_grievance'))

    return render_template('submit_grievance.html')


# ── Track Grievance (public) ──

@app.route('/track', methods=['GET', 'POST'])
def track_grievance():
    grievance = None
    if request.method == 'POST' or request.args.get('ticket_id'):
        ticket_id = request.form.get('ticket_id', '') or request.args.get('ticket_id', '')
        ticket_id = ticket_id.strip()
        grievance = Grievance.query.filter_by(ticket_id=ticket_id).first()
        if not grievance:
            flash('No grievance found with that ticket ID.', 'danger')
    return render_template('track.html', grievance=grievance)


# ── Grievance Detail ──

@app.route('/grievance/<int:gid>')
@login_required
def grievance_detail(gid):
    user = User.query.get(session['user_id'])
    grievance = Grievance.query.get_or_404(gid)

    # Access control
    if user.role == 'student' and grievance.student_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    authorities = User.query.filter(User.role.in_(['authority', 'admin'])).all()
    return render_template('grievance_detail.html', grievance=grievance, user=user, authorities=authorities)


# ── Update Grievance ──

@app.route('/grievance/<int:gid>/update', methods=['POST'])
@login_required
def update_grievance(gid):
    user = User.query.get(session['user_id'])
    grievance = Grievance.query.get_or_404(gid)

    message = request.form.get('message', '').strip()
    new_status = request.form.get('status', '')
    new_assignee = request.form.get('assigned_to', '')

    if new_status and user.role in ('authority', 'admin'):
        grievance.status = new_status
        if new_status in ('resolved', 'closed'):
            grievance.resolved_at = datetime.utcnow()

    if new_assignee and user.role == 'admin':
        grievance.assigned_to = int(new_assignee)

    if message:
        update = GrievanceUpdate(
            grievance_id=grievance.id,
            user_id=user.id,
            message=message,
            status_change=new_status if new_status else None
        )
        db.session.add(update)

    db.session.commit()
    flash('Grievance updated successfully.', 'success')
    return redirect(url_for('grievance_detail', gid=gid))


# ── Escalate Grievance ──

@app.route('/grievance/<int:gid>/escalate', methods=['POST'])
@login_required
def escalate_grievance(gid):
    grievance = Grievance.query.get_or_404(gid)
    grievance.status = 'escalated'
    grievance.escalation_level += 1

    # Reassign to admin on escalation
    admin = User.query.filter_by(role='admin').first()
    if admin:
        grievance.assigned_to = admin.id

    update = GrievanceUpdate(
        grievance_id=grievance.id,
        user_id=session.get('user_id'),
        message=f'Grievance escalated to level {grievance.escalation_level}. Reassigned to administration.',
        status_change='escalated'
    )
    db.session.add(update)
    db.session.commit()

    flash('Grievance has been escalated.', 'warning')
    return redirect(url_for('grievance_detail', gid=gid))


# ── Feedback ──

@app.route('/grievance/<int:gid>/feedback', methods=['POST'])
@login_required
def submit_feedback(gid):
    grievance = Grievance.query.get_or_404(gid)
    if grievance.feedback:
        flash('Feedback already submitted for this grievance.', 'info')
        return redirect(url_for('grievance_detail', gid=gid))

    rating = int(request.form.get('rating', 3))
    comment = request.form.get('comment', '').strip()

    feedback = Feedback(
        grievance_id=gid,
        user_id=session.get('user_id'),
        rating=rating,
        comment=comment
    )
    db.session.add(feedback)
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('grievance_detail', gid=gid))


# ── Admin: All Grievances ──

@app.route('/admin/grievances')
@role_required('admin')
def admin_grievances():
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')

    query = Grievance.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)

    grievances = query.order_by(Grievance.created_at.desc()).all()
    return render_template('admin_grievances.html', grievances=grievances,
                           status_filter=status_filter, category_filter=category_filter)


# ── Admin: Manage Users ──

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


# ── API: Chart Data ──

@app.route('/api/stats')
@login_required
def api_stats():
    """Return statistics for dashboard charts."""
    categories = ['academic', 'administrative', 'hostel', 'examination']
    statuses = ['submitted', 'in_review', 'in_progress', 'escalated', 'resolved', 'closed']

    cat_data = {}
    for c in categories:
        cat_data[c] = Grievance.query.filter_by(category=c).count()

    status_data = {}
    for s in statuses:
        status_data[s] = Grievance.query.filter_by(status=s).count()

    # Monthly trend (last 6 months)
    monthly = {}
    for i in range(5, -1, -1):
        d = datetime.utcnow() - timedelta(days=30 * i)
        label = d.strftime('%b %Y')
        start = d.replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            end = datetime.utcnow()
        else:
            next_month = (start + timedelta(days=32)).replace(day=1)
            end = next_month
        monthly[label] = Grievance.query.filter(
            Grievance.created_at >= start, Grievance.created_at < end
        ).count()

    return jsonify({'categories': cat_data, 'statuses': status_data, 'monthly': monthly})


# ─────────────────── Database Initialization ──────────────────

def init_db():
    """Create tables and seed default admin user."""
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@university.edu',
            password=generate_password_hash('admin123'),
            role='admin',
            department='administration'
        )
        db.session.add(admin)

        # Seed authority users for each category
        authorities = [
            ('academic_head', 'academic_head@university.edu', 'academic', 'Academic Department'),
            ('admin_officer', 'admin_officer@university.edu', 'administrative', 'Admin Office'),
            ('hostel_warden', 'hostel_warden@university.edu', 'hostel', 'Hostel Management'),
            ('exam_controller', 'exam_controller@university.edu', 'examination', 'Examination Cell'),
        ]
        for uname, email, dept, _ in authorities:
            user = User(
                username=uname,
                email=email,
                password=generate_password_hash('auth123'),
                role='authority',
                department=dept
            )
            db.session.add(user)

        db.session.commit()
        print("Database initialized with default users.")
        print("  Admin     -> username: admin, password: admin123")
        print("  Authority -> username: academic_head / admin_officer / hostel_warden / exam_controller, password: auth123")


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
