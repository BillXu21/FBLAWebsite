from flask_sqlalchemy import SQLAlchemy

# Initialize the database
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin', 'employer', or 'student'

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    bio = db.Column(db.Text)  # Short bio (or company description)
    skills = db.Column(db.String(255))  # Skills or experience
    profile_picture = db.Column(db.String(255))  # Path to profile picture

    phone_number = db.Column(db.String(20))
    birthday = db.Column(db.String(20))  # Can be stored as text or Date
    preferred_contact_method = db.Column(db.String(50))
    address = db.Column(db.String(255))
    education = db.Column(db.String(255))

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

class Applications(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    resume_path = db.Column(db.String(200))
    available_times = db.Column(db.Text)  # Free-form availability text
    experience = db.Column(db.Text)  # Past work experience
    birthday = db.Column(db.String(20))  # Optional birthday as text

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
