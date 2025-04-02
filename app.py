from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kayak_jobs.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database modellen
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    job_alerts = db.relationship('JobAlert', backref='user', lazy=True)

class JobAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    frequency = db.Column(db.String(20), default='daily')
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email is al geregistreerd')
            return redirect(url_for('register'))
            
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Ongeldige email of wachtwoord')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    alerts = JobAlert.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', alerts=alerts)

@app.route('/alert/new', methods=['GET', 'POST'])
@login_required
def new_alert():
    if request.method == 'POST':
        alert = JobAlert(
            user_id=current_user.id,
            search_query=request.form.get('search_query'),
            location=request.form.get('location'),
            frequency=request.form.get('frequency')
        )
        db.session.add(alert)
        db.session.commit()
        flash('Nieuwe job alert aangemaakt!')
        return redirect(url_for('dashboard'))
    return render_template('new_alert.html')

@app.route('/alert/<int:alert_id>/toggle')
@login_required
def toggle_alert(alert_id):
    alert = JobAlert.query.get_or_404(alert_id)
    if alert.user_id != current_user.id:
        return redirect(url_for('dashboard'))
    alert.is_active = not alert.is_active
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 