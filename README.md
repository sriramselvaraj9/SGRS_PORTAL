push co# Student Grievance Redressal System (SGRS)

A secure and centralized web-based grievance redressal system that allows students to submit complaints (anonymously or with identity), track resolution status in real-time, and enables authorities to manage and resolve grievances efficiently.

---

## Features

- **Grievance Submission** – Students can file grievances under 4 categories: Academic, Administrative, Hostel, and Examination.
- **Anonymous Complaints** – Option to submit grievances without revealing identity.
- **Automated Routing** – Complaints are auto-assigned to the relevant department authority.
- **Real-Time Status Tracking** – Track grievance status using a unique Ticket ID (no login needed).
- **Role-Based Access** – Three roles: Student, Authority, and Admin, each with tailored dashboards.
- **Escalation Mechanism** – Unsatisfied with progress? Escalate to higher authorities.
- **Feedback System** – Rate the resolution after a grievance is resolved.
- **Priority & Deadlines** – Priorities (Low/Medium/High/Urgent) with auto-calculated deadlines.
- **Admin Dashboard** – Charts, filters, user management, and overview of all grievances.
- **Responsive Design** – Works on desktop, tablet, and mobile devices.

---

## Tech Stack

| Component  | Technology        |
|------------|-------------------|
| Backend    | Python (Flask)    |
| Frontend   | HTML5, CSS3, JS   |
| Database   | SQLite            |
| Charts     | Chart.js          |
| Icons      | Font Awesome 6    |

---

## Project Structure

```
K project/
├── app.py                  # Main Flask application (routes, models, logic)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── static/
│   └── css/
│       └── style.css       # Complete stylesheet
├── templates/
│   ├── base.html           # Base template (navbar, footer, layout)
│   ├── index.html          # Landing/home page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Dashboard (student/authority/admin)
│   ├── submit_grievance.html  # Grievance submission form
│   ├── track.html          # Public grievance tracking page
│   ├── grievance_detail.html  # Detailed grievance view
│   ├── admin_grievances.html  # Admin: all grievances list
│   └── admin_users.html    # Admin: user management
└── instance/
    └── grievances.db       # SQLite database (auto-created on first run)
```

---

## How to Run the Project

### Prerequisites

- **Python 3.8+** installed on your system
- **pip** (Python package manager)

### Step-by-Step Instructions

#### 1. Open a Terminal / Command Prompt

Navigate to the project folder:

```bash
cd "K project"
```

#### 2. (Optional) Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Run the Application

```bash
python app.py
```

You will see output like:

```
Database initialized with default users.
  Admin     -> username: admin, password: admin123
  Authority -> username: academic_head / admin_officer / hostel_warden / exam_controller, password: auth123
 * Running on http://127.0.0.1:5000
```

#### 5. Open in Browser

Go to: **http://127.0.0.1:5000**

---

## Default Login Credentials

| Role      | Username          | Password   | Department      |
|-----------|-------------------|------------|-----------------|
| Admin     | admin             | admin123   | Administration  |
| Authority | academic_head     | auth123    | Academic        |
| Authority | admin_officer     | auth123    | Administrative  |
| Authority | hostel_warden     | auth123    | Hostel          |
| Authority | exam_controller   | auth123    | Examination     |

> You can also register as a new **Student** from the registration page.

---

## How to Use

### As a Student
1. **Register** a new account (select role: Student).
2. **Login** with your credentials.
3. **Submit a Grievance** – choose category, priority, and describe your issue.
4. **Track Status** – view your grievances on the dashboard or use Ticket ID to track publicly.
5. **Escalate** if not satisfied with the response.
6. **Give Feedback** once your grievance is resolved.

### As an Authority
1. **Login** with authority credentials.
2. **View Assigned Grievances** on your dashboard.
3. **Update Status** – add responses, change status to In Review / In Progress / Resolved.
4. **View Charts** for your assigned grievances.

### As an Admin
1. **Login** with admin credentials.
2. **View All Grievances** with filter and search capabilities.
3. **Reassign** grievances to different authorities.
4. **Manage Users** – view all registered users.
5. **Monitor Dashboard** – charts showing category distribution, status breakdown, and monthly trends.

### Anonymous Submission (No Login Required)
1. Go to **Submit Grievance** from the homepage.
2. Check the **"Submit Anonymously"** checkbox.
3. Save your **Ticket ID** to track the grievance later.

---

## Grievance Workflow

```
Submit → Auto-Assign → In Review → In Progress → Resolved → Closed
                                         ↓
                                    Escalated (reassigned to Admin)
```

### Priority-Based Deadlines

| Priority | Resolution Deadline |
|----------|---------------------|
| Low      | 14 days             |
| Medium   | 7 days              |
| High     | 3 days              |
| Urgent   | 1 day               |

---

## Screenshots

Once running, you can explore:
- **Home Page**: `http://127.0.0.1:5000/`
- **Register**: `http://127.0.0.1:5000/register`
- **Login**: `http://127.0.0.1:5000/login`
- **Dashboard**: `http://127.0.0.1:5000/dashboard`
- **Submit Grievance**: `http://127.0.0.1:5000/grievance/new`
- **Track Grievance**: `http://127.0.0.1:5000/track`

---

## License

This project is developed for educational purposes as part of a student project.
