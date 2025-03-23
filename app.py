from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import text

from database_manager import db, init_db, User, JobPostings, Applications  # Import models from database_manager
from messages import messages_bp  # Import messages blueprint
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SECRET_KEY'] = "c4503c9ea5c353527f6ffa75dbde1b9dc1d4973fc171584a6b590a354bafeefa"
init_db(app)

# Register blueprints
app.register_blueprint(messages_bp, url_prefix='/messages')


UPLOAD_FOLDER = 'uploads/resumes'  # Store resumes in this folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Routes
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register')
def register():
    """Render the main registration page where users choose between Student or Employer registration."""
    return render_template('register.html')


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        bio = request.form.get('bio', '')
        skills = request.form.get('skills', '')
        phone_number = request.form.get('phone_number', '')
        birthday = request.form.get('birthday', '')
        preferred_contact_method = request.form.get('preferred_contact_method', '')
        address = request.form.get('address', '')
        education = request.form.get('education', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_student'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            user_type='student',
            bio=bio,
            skills=skills,
            phone_number=phone_number,
            birthday=birthday,
            preferred_contact_method=preferred_contact_method,
            address=address,
            education=education,
            profile_picture=""
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Student account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register_student.html')


@app.route('/register_employer', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        bio = request.form['bio']  # company description
        phone_number = request.form.get('phone_number', '')
        birthday = request.form.get('birthday', '')
        preferred_contact_method = request.form.get('preferred_contact_method', '')
        address = request.form.get('address', '')
        education = request.form.get('education', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_employer'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_employer = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            user_type='employer',
            bio=bio,
            phone_number=phone_number,
            birthday=birthday,
            preferred_contact_method=preferred_contact_method,
            address=address,
            education=education,
            skills=None,
            profile_picture=""
        )

        db.session.add(new_employer)
        db.session.commit()

        flash('Employer account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register_employer.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.user_type == 'admin'
            session['user_type'] = user.user_type  # Store user_type in session
            return redirect(url_for('home'))
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

@app.route('/employer_form', methods=['GET', 'POST'])
def employer_form():
    if session.get('user_type') not in ['employer', 'admin']:
        return "Access denied", 403

    if request.method == 'POST':
        new_job = JobPostings(
            company_name=request.form['company_name'],
            job_title=request.form['job_title'],
            description=request.form['description'],
            skills=request.form['skills'],
            salary=request.form.get('salary', 'Not specified'),
            status="pending",  # Set status to pending
            employer_email=session.get('user_id')  # Associate job with employer
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('job_listings'))
    return render_template('employer_form.html')

@app.route('/job_listings')
def job_listings():
    try:
        jobs = JobPostings.query.filter_by(status="approved").all()
    except Exception as e:
        print(f"Error fetching job listings: {e}")
        jobs = []
    return render_template('job_listings.html', jobs=jobs)

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if not session.get('is_admin'):
        return "Access denied", 403
    job = JobPostings.query.get(job_id)
    if job:
        db.session.delete(job)
        db.session.commit()
    return redirect(url_for('job_listings'))

'''@app.route('/confirm_delete/<int:job_id>', methods=['GET', 'POST'])
def confirm_delete(job_id):
    if request.method == 'POST':
        return redirect(url_for('delete_job', job_id=job_id))
    job = JobPostings.query.get(job_id)
    return render_template('confirm_delete.html', job=job)'''

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('is_admin'):
        return "Access denied", 403

    if request.method == 'POST':
        action = request.form['action']
        job_id = int(request.form['job_id'])
        job = JobPostings.query.get(job_id)
        if job:
            if action == 'approve':
                job.status = 'approved'
            elif action == 'delete':
                db.session.delete(job)
            db.session.commit()

    # Pass pending jobs to the template
    pending_jobs = JobPostings.query.filter_by(status="pending").all()
    return render_template('admin_panel.html', jobs=pending_jobs)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_to_job(job_id):
    if 'user_id' not in session or session.get('user_type') != 'student':
        flash("You must be logged in as a student to apply for a job.", "danger")
        return redirect(url_for('login'))

    job = JobPostings.query.get_or_404(job_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        birthday = request.form.get('birthday')
        availability = request.form.get('availability')
        experience = request.form.get('experience')
        cover_letter = request.form.get('cover_letter')
        resume = request.files['resume']

        resume_path = None
        if resume:
            filename = secure_filename(resume.filename)
            resume_path = os.path.join('static', 'resumes', filename)
            resume.save(resume_path)

        application = Applications(
            job_id=job_id,
            name=name,
            email=email,
            birthday=birthday,
            availability=availability,
            experience=experience,
            cover_letter=cover_letter,
            resume_path=resume_path
        )

        db.session.add(application)
        db.session.commit()
        flash("Application submitted successfully!", "success")
        return redirect(url_for('job_listings'))

    return render_template('apply_form.html', job=job)


@app.route('/notifications')
def get_notifications():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'notifications': []})

    notifications = db.session.execute(
        text("""
            SELECT 
                CASE 
                    WHEN c.participant1_id = :user_id THEN u2.email
                    ELSE u1.email 
                END AS sender_email,
                SUM(c.notifications) AS total_notifications,  -- Aggregate notifications per sender
                c.shared_id  -- Include shared conversation ID
            FROM conversations c
            JOIN user u1 ON c.participant1_id = u1.id
            JOIN user u2 ON c.participant2_id = u2.id
            WHERE (c.participant1_id = :user_id)
            AND c.notifications > 0
            GROUP BY sender_email, c.shared_id  -- Grouping by sender and conversation ID
        """), {'user_id': user_id}
    ).fetchall()

    notifications_list = [{'sender': row[0], 'count': row[1], 'conversation_id': row[2]} for row in notifications]

    return jsonify({'notifications': notifications_list})


@app.route('/notifications/count')
def get_notification_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'count': 0})

    notification_count = db.session.execute(
        text("""
            SELECT SUM(notifications) 
            FROM conversations 
            WHERE participant2_id = :user_id
        """), {'user_id': user_id}
    ).scalar() or 0

    return jsonify({'count': notification_count})

@app.route('/applications/notifications')
def get_application_notifications():
    """
    Retrieves the count of new job applications for an employer.
    """
    employer_email = session.get('user_email')
    if not employer_email:
        return jsonify({'count': 0})

    notification_count = db.session.execute(
        text("""
            SELECT COUNT(*) FROM applications a
            JOIN job_postings j ON a.job_id = j.id
            WHERE j.employer_email = :employer_email
        """), {'employer_email': employer_email}
    ).scalar() or 0

    return jsonify({'count': notification_count})

@app.route('/employer/applications')
def view_applications():
    user_id = session.get('user_id')
    if not user_id or session.get('user_type') != 'employer':
        return "Unauthorized", 403

    applications = db.session.execute(
        text("""
            SELECT a.id, a.cover_letter, a.resume_path, a.available_times, a.experience, a.birthday,
                   u.first_name, u.last_name, u.email, u.skills, u.education
            FROM applications a
            JOIN user u ON a.applicant_id = u.id
            JOIN job_postings j ON a.job_id = j.id
            WHERE j.employer_email = :employer_id
        """),
        {"employer_id": user_id}
    ).fetchall()

    return render_template("employer_applications.html", applications=applications)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    """
    Displays the profile page for a user.
    """
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
