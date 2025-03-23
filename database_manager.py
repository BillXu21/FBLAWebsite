from flask_sqlalchemy import SQLAlchemy

# Initialize the database
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    """Represents a user in the system, including students and employers."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin', 'employer', or 'student'

    # Additional profile fields
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    bio = db.Column(db.Text)  # Short bio (optional)
    skills = db.Column(db.String(255))  # Relevant skills (only for students)
    company_name = db.Column(db.String(255))  # Employer-specific field (only for employers)
    profile_picture = db.Column(db.String(255), default="")  # Path to profile picture (default empty)

# Define the JobPostings model
class JobPostings(db.Model):
    """Represents job postings submitted by employers."""
    __tablename__ = 'job_postings'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.Numeric(10, 2))  # Numeric salary field
    status = db.Column(db.String(20), default="pending")  # Status: pending/approved
    employer_email = db.Column(db.String(100), nullable=False)  # Employer who posted the job

# Define the Applications model
class Applications(db.Model):
    """Represents job applications submitted by students."""
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Applicant's name
    email = db.Column(db.String(100), nullable=False)  # Applicant's email
    resume_path = db.Column(db.String(200))  # File path to resume (optional)

# Define the Conversations model for messaging
class Conversation(db.Model):
    """Represents a private conversation between two users."""
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    participant1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_id = db.Column(db.Integer, nullable=False)  # Shared ID for both participants
    unread_count = db.Column(db.Integer, default=0, nullable=False)  # Unread messages count
    messages = db.relationship('Message', backref='conversation', lazy=True)

# Define the Messages model for individual messages
class Message(db.Model):
    """Represents individual messages exchanged in a conversation."""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Message text
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

# Initialize the database with Flask app
def init_db(app):
    """Initializes the database tables within the given Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
