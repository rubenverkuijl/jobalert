from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import secrets
from config import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config.from_object(config['production'])
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin check decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email != os.getenv('ADMIN_EMAIL'):
            flash('U heeft geen toegang tot deze pagina.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Database modellen
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
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

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Genereer een unieke reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Stuur e-mail met reset link
            reset_url = url_for('reset_password', token=token, _external=True)
            send_reset_email(user.email, reset_url)
            
            flash('Er is een e-mail verstuurd met instructies om uw wachtwoord te resetten.')
            return redirect(url_for('login'))
        else:
            flash('Geen account gevonden met dit e-mailadres.')
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(reset_token=token).first()
        
        if user and user.reset_token_expiry > datetime.utcnow():
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            
            flash('Uw wachtwoord is succesvol gewijzigd. U kunt nu inloggen.')
            return redirect(url_for('login'))
        else:
            flash('De reset link is ongeldig of verlopen.')
            return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html')

def send_reset_email(email, reset_url):
    sender_email = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = 'Wachtwoord Reset Kayak Job Alerts'
    
    body = f"""Hallo,

Er is een wachtwoord reset aangevraagd voor uw Kayak Job Alerts account.
Klik op de volgende link om uw wachtwoord te resetten:

{reset_url}

Als u geen wachtwoord reset heeft aangevraagd, kunt u deze e-mail negeren.

Met vriendelijke groet,
Kayak Job Alerts Team
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print(f"Reset e-mail succesvol verzonden naar {email}")
    except Exception as e:
        print(f"Fout bij het verzenden van de reset e-mail: {str(e)}")

@app.route('/test/email')
@login_required
@admin_required
def test_email():
    try:
        # Test e-mail versturen
        test_jobs = [{
            'title': 'Test Vacature',
            'company': 'Test Bedrijf',
            'location': 'Test Locatie'
        }]
        
        send_job_alert(current_user.email, 'TEST ALERT', test_jobs)
        flash('Test e-mail succesvol verzonden!')
    except Exception as e:
        flash(f'Fout bij versturen test e-mail: {str(e)}')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 