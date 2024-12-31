from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
db = SQLAlchemy(app)

# Database models
class JobPostings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.String(50))
    status = db.Column(db.String(20), default="pending")

class Applications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    resume_path = db.Column(db.String(200))

# Routes
@app.route('/')
def home():
    return "Welcome to the Job Portal"

@app.route('/employer_form', methods=['GET', 'POST'])
def employer_form():
    if request.method == 'POST':
        new_job = JobPostings(
            company_name=request.form['company_name'],
            job_title=request.form['job_title'],
            description=request.form['description'],
            skills=request.form['skills'],
            salary=request.form.get('salary', 'Not specified')
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('job_listings'))
    return render_template('employer_form.html')

@app.route('/job_listings')
def job_listings():
    jobs = JobPostings.query.filter_by(status="approved").all()
    return render_template('job_listings.html', jobs=jobs)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        action = request.form['action']
        job_id = int(request.form['job_id'])
        job = JobPostings.query.get(job_id)
        if action == 'approve':
            job.status = 'approved'
        elif action == 'delete':
            db.session.delete(job)
        db.session.commit()
    pending_jobs = JobPostings.query.filter_by(status="pending").all()
    return render_template('admin_panel.html', jobs=pending_jobs)

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
