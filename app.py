import secrets
import random

import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from datetime import timedelta

import os

import csv

from io import StringIO

from datetime import datetime, date, timedelta

from functools import wraps



from flask import (

    Flask, render_template, redirect, url_for, request,

    flash, jsonify, session, make_response

)

from flask_login import (

    LoginManager, UserMixin, login_user, login_required,

    logout_user, current_user

)

from werkzeug.security import generate_password_hash, check_password_hash

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature



from database.connection import get_db

from database.init_db import init_db

from database.seed import seed_data



app = Flask(__name__)

app.config['SECRET_KEY'] = 'fleetflow-master-secure-key-2026'



serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# -------------------------------------------------------------
# OTP GENERATION & DISPATCH HELPERS
# -------------------------------------------------------------

def generate_secure_otp():
    """Generates a cryptographically secure 6-digit numeric OTP using secrets."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def send_otp_email(to_email, otp_code, user_name="FleetFlow User"):
    """
    Sends 6-digit OTP verification email via SMTP credentials configured in .env.
    Falls back gracefully to secure console logging during offline local testing.
    """
    mail_server = os.environ.get('MAIL_SERVER', os.environ.get('SMTP_SERVER', 'smtp.gmail.com'))
    mail_port = int(os.environ.get('MAIL_PORT', os.environ.get('SMTP_PORT', 587)))
    mail_user = os.environ.get('MAIL_USERNAME', os.environ.get('SMTP_USER', ''))
    mail_password = os.environ.get('MAIL_PASSWORD', os.environ.get('SMTP_PASSWORD', ''))
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    mail_use_ssl = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 'yes']
    sender = os.environ.get('MAIL_DEFAULT_SENDER', mail_user or 'noreply@fleetflow.com')

    subject = f"FleetFlow Password Reset Verification Code: {otp_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .logo-badge {{ background: #4f46e5; color: white; display: inline-block; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-bottom: 16px; }}
            .otp-box {{ background: #f1f5f9; border: 2px dashed #6366f1; border-radius: 8px; padding: 18px; text-align: center; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #4338ca; margin: 24px 0; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div style="text-align: center;">
                <div class="logo-badge">FleetFlow Master</div>
                <h2 style="color: #0f172a; margin: 8px 0; font-size: 20px;">Password Reset Verification</h2>
                <p style="color: #64748b; font-size: 14px;">Hello {user_name}, you requested a password reset for your FleetFlow account.</p>
            </div>
            <p style="color: #475569; font-size: 13.5px; text-align: center;">Use the 6-digit one-time verification code below. This code is valid for <strong>5 minutes</strong>.</p>
            <div class="otp-box">{otp_code}</div>
            <p style="color: #64748b; font-size: 12.5px; text-align: center;">Never share this code with anyone. If you did not make this request, you can safely ignore this email.</p>
            <div class="footer">
                &copy; 2026 FleetFlow Master OS &bull; Automated Fleet & Logistics Management
            </div>
        </div>
    </body>
    </html>
    """

    email_sent = False
    if mail_user and mail_password:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = to_email
            msg.attach(MIMEText(f"Your FleetFlow password reset OTP is: {otp_code}. Valid for 5 minutes.", 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            if mail_use_ssl:
                with smtplib.SMTP_SSL(mail_server, mail_port, timeout=10) as server:
                    server.login(mail_user, mail_password)
                    server.sendmail(sender, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
                    if mail_use_tls:
                        server.starttls()
                    server.login(mail_user, mail_password)
                    server.sendmail(sender, [to_email], msg.as_string())
            email_sent = True
            print(f"[EMAIL] Verification OTP successfully sent to {to_email}")
        except Exception as e:
            print(f"[EMAIL NOTIFICATION] Live SMTP dispatch failed ({e}). Logged to terminal.")

    # Always log OTP in development console for easy copy-paste
    print(f"\n==========================================")
    print(f" [FLEETFLOW EMAIL OTP DISPATCH]")
    print(f" Recipient: {to_email}")
    print(f" 6-Digit OTP: >>> {otp_code} <<<")
    print(f" Valid For: 5 Minutes (Expires at: {datetime.now() + timedelta(minutes=5)})")
    print(f"==========================================\n")
    return email_sent




login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'

login_manager.login_message = 'Please sign in to access FleetFlow.'

login_manager.login_message_category = 'warning'



class User(UserMixin):

    def __init__(self, id, email, role, name, is_active=1):

        self.id = id

        self.email = email

        self.role = role

        self.name = name

        self._is_active = is_active



    @property

    def is_active(self):

        return bool(self._is_active)



    def get_id(self):

        return str(self.id)



@login_manager.user_loader

def load_user(user_id):

    conn = get_db()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    conn.close()

    if user:

        return User(user['id'], user['email'], user['role'], user['name'], user['is_active'])

    return None



def role_required(*roles):

    def decorator(f):

        @wraps(f)

        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:

                flash('Please log in to access this page.', 'warning')

                return redirect(url_for('login'))

            if current_user.role not in roles:

                flash(f'Access denied. Role "{current_user.role}" does not have sufficient permissions.', 'danger')

                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator



@app.context_processor

def utility_processor():

    def get_today():

        return date.today().isoformat()



    def is_expired(expiry_date):

        if not expiry_date:

            return False

        try:

            exp = datetime.strptime(str(expiry_date)[:10], '%Y-%m-%d').date()

            return exp < date.today()

        except Exception:

            return False



    def days_until(expiry_date):

        if not expiry_date:

            return None

        try:

            exp = datetime.strptime(str(expiry_date)[:10], '%Y-%m-%d').date()

            return (exp - date.today()).days

        except Exception:

            return None



    return dict(today=get_today, is_expired=is_expired, days_until=days_until)



# -------------------------------------------------------------

# AUTH & ROLE SWITCHING (PAGE 1)

# -------------------------------------------------------------



@app.route('/')

@app.route('/home')

def home():

    return render_template('home.html')



@app.route('/login', methods=['GET', 'POST'])

def login():

    if current_user.is_authenticated:

        return redirect(url_for('dashboard'))



    if request.method == 'POST':

        email = request.form.get('email', '').strip()

        password = request.form.get('password', '')



        conn = get_db()

        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()



        if user and check_password_hash(user['password'], password):

            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))

            conn.commit()

            conn.close()



            user_obj = User(user['id'], user['email'], user['role'], user['name'], user['is_active'])

            login_user(user_obj)

            flash(f'Welcome back, {user["name"]}! Logged in as {user["role"]}.', 'success')

            return redirect(url_for('dashboard'))

        else:

            conn.close()

            flash('Invalid email or password. Please try again.', 'danger')



    return render_template('auth/login.html')





@app.route('/register', methods=['GET', 'POST'])

def register():

    if current_user.is_authenticated:

        return redirect(url_for('dashboard'))



    if request.method == 'POST':

        name = request.form.get('name', '').strip()

        email = request.form.get('email', '').strip()

        role = request.form.get('role', 'Dispatcher')

        password = request.form.get('password', '')

        confirm_password = request.form.get('confirm_password', '')



        if not name or not email or not password:

            flash('All fields are required.', 'danger')

            return render_template('auth/register.html')



        if password != confirm_password:

            flash('Passwords do not match.', 'danger')

            return render_template('auth/register.html')



        if len(password) < 6:

            flash('Password must be at least 6 characters long.', 'danger')

            return render_template('auth/register.html')



        conn = get_db()

        existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()

        if existing:

            conn.close()

            flash('An account with this email address already exists.', 'danger')

            return render_template('auth/register.html')



        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (name, email, password, role, is_active) VALUES (?, ?, ?, ?, 1)", (name, email, hashed_pw, role))

        user_id = cursor.lastrowid

        conn.commit()

        conn.close()



        user_obj = User(user_id, email, role, name, 1)

        login_user(user_obj)



        flash(f'Account created successfully! Welcome to FleetFlow, {name}.', 'success')

        return redirect(url_for('dashboard'))



    return render_template('auth/register.html')



@app.route('/switch-role/<role>')

def switch_role(role):

    valid_roles = ['Manager', 'Dispatcher', 'Safety Officer', 'Financial Analyst']

    if role not in valid_roles:

        flash('Invalid role selected.', 'danger')

        return redirect(url_for('dashboard'))



    conn = get_db()

    user = conn.execute('SELECT * FROM users WHERE role = ? LIMIT 1', (role,)).fetchone()

    conn.close()



    if user:

        user_obj = User(user['id'], user['email'], user['role'], user['name'], user['is_active'])

        login_user(user_obj)

        flash(f'Switched session to {user["name"]} ({role}).', 'info')

    return redirect(url_for('dashboard'))





def send_otp_email(to_email, otp_code, user_name="Valued User"):

    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')

    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    smtp_user = os.environ.get('SMTP_USER', '')

    smtp_password = os.environ.get('SMTP_PASSWORD', '')

    sender_email = os.environ.get('SMTP_FROM', smtp_user or 'noreply@fleetflow.com')



    subject = f"FleetFlow Password Reset OTP: {otp_code}"

    

    html_content = f"""

    <!DOCTYPE html>

    <html>

    <head>

        <style>

            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; }}

            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}

            .header {{ text-align: center; margin-bottom: 24px; }}

            .logo {{ background: #4f46e5; color: white; display: inline-block; padding: 10px 16px; border-radius: 8px; font-weight: bold; font-size: 18px; }}

            .otp-box {{ background: #f1f5f9; border: 2px dashed #6366f1; border-radius: 8px; padding: 18px; text-align: center; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #4338ca; margin: 24px 0; }}

            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}

        </style>

    </head>

    <body>

        <div class="container">

            <div class="header">

                <div class="logo">FleetFlow Master</div>

                <h2 style="color: #1e293b; margin-top: 16px; font-size: 20px;">Password Reset Verification</h2>

                <p style="color: #64748b; font-size: 14px;">Hello {user_name}, you requested a password reset for your FleetFlow account.</p>

            </div>

            <p style="color: #475569; font-size: 14px; text-align: center;">Use the one-time verification code below to reset your password. This code will expire in <strong>10 minutes</strong>.</p>

            <div class="otp-box">{otp_code}</div>

            <p style="color: #64748b; font-size: 13px; text-align: center;">If you did not request this password reset, please disregard this email.</p>

            <div class="footer">

                &copy; 2026 FleetFlow Master OS &bull; Automated Fleet & Logistics Hub

            </div>

        </div>

    </body>

    </html>

    """



    email_sent = False

    if smtp_user and smtp_password:

        try:

            msg = MIMEMultipart('alternative')

            msg['Subject'] = subject

            msg['From'] = sender_email

            msg['To'] = to_email

            msg.attach(MIMEText(f"Your FleetFlow password reset OTP is: {otp_code}. Valid for 10 minutes.", 'plain'))

            msg.attach(MIMEText(html_content, 'html'))



            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:

                server.starttls()

                server.login(smtp_user, smtp_password)

                server.sendmail(sender_email, [to_email], msg.as_string())

            email_sent = True

            print(f"[EMAIL] Password reset OTP sent to {to_email} via SMTP")

        except Exception as e:

            print(f"[EMAIL ERROR] Failed to send live email: {e}")

    

    print(f"\n==========================================")

    print(f" [FLEETFLOW OTP DISPATCH]")

    print(f" Recipient: {to_email}")

    print(f" Verification OTP: >>> {otp_code} <<<")

    print(f" Expires In: 10 Minutes")

    print(f"==========================================\n")

    return email_sent






@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('login'))


# -------------------------------------------------------------
# FORGOT PASSWORD & EMAIL OTP WORKFLOW
# -------------------------------------------------------------

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/forgot_password.html')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE LOWER(email) = ?', (email,)).fetchone()
        
        # If user exists, generate OTP and send email
        if user:
            # Check 60-second resend cooldown
            last_record = conn.execute('''
                SELECT created_at FROM password_resets 
                WHERE LOWER(email) = ? 
                ORDER BY id DESC LIMIT 1
            ''', (email,)).fetchone()

            if last_record and last_record['created_at']:
                try:
                    last_time = datetime.strptime(str(last_record['created_at'])[:19], '%Y-%m-%d %H:%M:%S')
                    elapsed = (datetime.now() - last_time).total_seconds()
                    if elapsed < 60:
                        conn.close()
                        session['reset_email'] = email
                        flash(f'Please wait {int(60 - elapsed)} seconds before requesting another OTP.', 'warning')
                        return redirect(url_for('verify_otp'))
                except Exception:
                    pass

            # Generate secure 6-digit OTP using secrets module
            otp_code = generate_secure_otp()
            otp_hash = generate_password_hash(otp_code, method='pbkdf2:sha256')
            expires_at = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

            # Invalidate older unused OTPs
            conn.execute('UPDATE password_resets SET is_used = 1 WHERE LOWER(email) = ?', (email,))
            conn.execute('''
                INSERT INTO password_resets (email, otp_hash, expires_at, attempts_count, is_used)
                VALUES (?, ?, ?, 0, 0)
            ''', (email, otp_hash, expires_at))
            conn.commit()

            # Dispatch Email OTP
            send_otp_email(email, otp_code, user['name'])

        conn.close()
        
        # Generic response to prevent user enumeration
        session['reset_email'] = email
        flash('If an account exists with this email address, a 6-digit verification code has been sent.', 'info')
        return redirect(url_for('verify_otp'))

    return render_template('auth/forgot_password.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    email = session.get('reset_email', '')
    if not email:
        flash('Please initiate password recovery first.', 'warning')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        if not otp_input or len(otp_input) != 6:
            flash('Please enter the complete 6-digit OTP verification code.', 'danger')
            return render_template('auth/verify_otp.html', email=email)

        conn = get_db()
        record = conn.execute('''
            SELECT * FROM password_resets 
            WHERE LOWER(email) = ? AND is_used = 0 
            ORDER BY id DESC LIMIT 1
        ''', (email.lower(),)).fetchone()

        if not record:
            conn.close()
            flash('No active OTP found or code has already been used. Please request a new code.', 'danger')
            return redirect(url_for('forgot_password'))

        # Check maximum 5 incorrect attempts
        if record['attempts_count'] >= 5:
            conn.execute('UPDATE password_resets SET is_used = 1 WHERE id = ?', (record['id'],))
            conn.commit()
            conn.close()
            flash('Maximum verification attempts (5) exceeded. This OTP has been locked for security. Please request a new code.', 'danger')
            return redirect(url_for('forgot_password'))

        # Check 5-minute expiry
        try:
            exp_time = datetime.strptime(str(record['expires_at'])[:19], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > exp_time:
                conn.execute('UPDATE password_resets SET is_used = 1 WHERE id = ?', (record['id'],))
                conn.commit()
                conn.close()
                flash('The OTP verification code has expired (5 minute limit). Please request a fresh code.', 'danger')
                return redirect(url_for('forgot_password'))
        except Exception as e:
            pass

        # Verify hashed OTP match
        if not check_password_hash(record['otp_hash'], otp_input):
            new_attempts = record['attempts_count'] + 1
            conn.execute('UPDATE password_resets SET attempts_count = ? WHERE id = ?', (new_attempts, record['id']))
            conn.commit()
            conn.close()

            remaining = 5 - new_attempts
            if remaining <= 0:
                flash('Maximum incorrect attempts reached. This OTP has been invalidated.', 'danger')
                return redirect(url_for('forgot_password'))
            else:
                flash(f'Incorrect OTP verification code. {remaining} attempt(s) remaining.', 'danger')
                return render_template('auth/verify_otp.html', email=email)

        # OTP Verified successfully: Invalidate OTP and issue single-use reset token
        conn.execute('UPDATE password_resets SET is_used = 1 WHERE id = ?', (record['id'],))
        conn.commit()
        conn.close()

        reset_token = secrets.token_hex(24)
        session['otp_verified_token'] = reset_token
        session['otp_verified_email'] = email

        flash('Identity verified successfully! Please enter your new password below.', 'success')
        return redirect(url_for('reset_password'))

    return render_template('auth/verify_otp.html', email=email)


@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    email = request.form.get('email') or session.get('reset_email', '')
    if not email:
        flash('Session expired. Please enter your email to request an OTP.', 'warning')
        return redirect(url_for('forgot_password'))

    conn = get_db()
    # Check 60-second cooldown
    last_record = conn.execute('''
        SELECT created_at FROM password_resets 
        WHERE LOWER(email) = ? 
        ORDER BY id DESC LIMIT 1
    ''', (email.lower(),)).fetchone()

    if last_record and last_record['created_at']:
        try:
            last_time = datetime.strptime(str(last_record['created_at'])[:19], '%Y-%m-%d %H:%M:%S')
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < 60:
                conn.close()
                flash(f'Please wait {int(60 - elapsed)} seconds before requesting a new OTP.', 'warning')
                return redirect(url_for('verify_otp'))
        except Exception:
            pass

    user = conn.execute('SELECT * FROM users WHERE LOWER(email) = ?', (email.lower(),)).fetchone()
    if user:
        otp_code = generate_secure_otp()
        otp_hash = generate_password_hash(otp_code, method='pbkdf2:sha256')
        expires_at = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

        conn.execute('UPDATE password_resets SET is_used = 1 WHERE LOWER(email) = ?', (email.lower(),))
        conn.execute('''
            INSERT INTO password_resets (email, otp_hash, expires_at, attempts_count, is_used)
            VALUES (?, ?, ?, 0, 0)
        ''', (email.lower(), otp_hash, expires_at))
        conn.commit()

        send_otp_email(email.lower(), otp_code, user['name'])

    conn.close()
    flash('A fresh 6-digit verification code has been dispatched to your email.', 'info')
    return redirect(url_for('verify_otp'))


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    # Strict protection: Ensure user passed OTP verification
    verified_token = session.get('otp_verified_token')
    verified_email = session.get('otp_verified_email')

    if not verified_token or not verified_email:
        flash('Unauthorized access. Please verify your email OTP first.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            flash('All password fields are required.', 'danger')
            return render_template('auth/reset_password.html')

        if new_password != confirm_password:
            flash('Passwords do not match. Please verify and try again.', 'danger')
            return render_template('auth/reset_password.html')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html')

        # Hash new password with pbkdf2:sha256 and update user
        hashed_pw = generate_password_hash(new_password, method='pbkdf2:sha256')
        conn = get_db()
        conn.execute('UPDATE users SET password = ? WHERE LOWER(email) = ?', (hashed_pw, verified_email.lower()))
        conn.commit()
        conn.close()

        # Clean up all verification session state
        session.pop('reset_email', None)
        session.pop('otp_verified_token', None)
        session.pop('otp_verified_email', None)

        flash('Your password has been successfully updated! You can now log in with your new credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action', 'update_info')

        if action == 'update_info':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Name cannot be empty.', 'danger')
            else:
                conn.execute('UPDATE users SET name = ? WHERE id = ?', (name, current_user.id))
                conn.commit()
                current_user.name = name
                flash('Profile information updated successfully!', 'success')

        elif action == 'update_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            user_row = conn.execute('SELECT password FROM users WHERE id = ?', (current_user.id,)).fetchone()

            if not check_password_hash(user_row['password'], current_pw):
                flash('Current password entered is incorrect.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            else:
                hashed_pw = generate_password_hash(new_pw, method='pbkdf2:sha256')
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, current_user.id))
                conn.commit()
                flash('Your password has been updated successfully!', 'success')

        conn.close()
        return redirect(url_for('profile'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    return redirect(url_for('profile'))

@app.route('/dashboard')

@login_required

def dashboard():

    conn = get_db()



    active_fleet = conn.execute("SELECT COUNT(*) as count FROM vehicles WHERE status = 'On Trip'").fetchone()['count']

    in_shop = conn.execute("SELECT COUNT(*) as count FROM vehicles WHERE status = 'In Shop'").fetchone()['count']

    total_vehicles = conn.execute("SELECT COUNT(*) as count FROM vehicles WHERE status != 'Retired'").fetchone()['count']

    pending_cargo = conn.execute("SELECT COUNT(*) as count FROM trips WHERE status = 'Draft'").fetchone()['count']



    utilization_rate = round((active_fleet / total_vehicles * 100), 1) if total_vehicles > 0 else 0



    fleet_vehicles = conn.execute("SELECT * FROM vehicles ORDER BY status ASC, name ASC").fetchall()



    recent_trips = conn.execute('''

        SELECT t.*, v.name as vehicle_name, v.license_plate, d.name as driver_name

        FROM trips t

        JOIN vehicles v ON t.vehicle_id = v.id

        JOIN drivers d ON t.driver_id = d.id

        ORDER BY t.id DESC LIMIT 8

    ''').fetchall()



    conn.close()



    return render_template(

        'dashboard.html',

        active_fleet=active_fleet,

        in_shop=in_shop,

        utilization_rate=utilization_rate,

        total_vehicles=total_vehicles,

        pending_cargo=pending_cargo,

        fleet_vehicles=fleet_vehicles,

        recent_trips=recent_trips

    )



# -------------------------------------------------------------

# PAGE 3: VEHICLE REGISTRY (ASSET MANAGEMENT)

# -------------------------------------------------------------



@app.route('/vehicles')

@login_required

def vehicles():

    conn = get_db()

    vehicles_list = conn.execute("SELECT * FROM vehicles ORDER BY id DESC").fetchall()

    conn.close()

    return render_template('vehicles.html', vehicles=vehicles_list)



@app.route('/vehicles/add', methods=['POST'])

@login_required

@role_required('Manager')

def add_vehicle():

    name = request.form.get('name', '').strip()

    model = request.form.get('model', '').strip()

    license_plate = request.form.get('license_plate', '').strip().upper()

    v_type = request.form.get('type')

    max_capacity = float(request.form.get('max_capacity', 0))

    odometer = int(request.form.get('odometer', 0))

    acquisition_cost = float(request.form.get('acquisition_cost', 0))

    region = request.form.get('region', 'Central')



    conn = get_db()

    try:

        conn.execute('''

            INSERT INTO vehicles (name, model, license_plate, type, max_capacity, odometer, acquisition_cost, region, status)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Available')

        ''', (name, model, license_plate, v_type, max_capacity, odometer, acquisition_cost, region))

        conn.commit()

        flash(f'Vehicle "{name}" ({license_plate}) registered successfully as Available.', 'success')

    except Exception as e:

        flash(f'Error adding vehicle: License plate must be unique ({e}).', 'danger')

    finally:

        conn.close()



    return redirect(url_for('vehicles'))



@app.route('/vehicles/<int:vehicle_id>/toggle-status', methods=['POST'])

@login_required

@role_required('Manager')

def toggle_vehicle_status(vehicle_id):

    conn = get_db()

    v = conn.execute('SELECT status, name FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()

    if v:

        new_status = 'Available' if v['status'] == 'Retired' else 'Retired'

        conn.execute('UPDATE vehicles SET status = ? WHERE id = ?', (new_status, vehicle_id))

        conn.commit()

        flash(f'Vehicle "{v["name"]}" status updated to {new_status}.', 'info')

    conn.close()

    return redirect(url_for('vehicles'))



# -------------------------------------------------------------

# PAGE 4: TRIP DISPATCHER & MANAGEMENT

# -------------------------------------------------------------



@app.route('/trips')

@login_required

def trips():

    conn = get_db()

    trips_list = conn.execute('''

        SELECT t.*, v.name as vehicle_name, v.max_capacity as vehicle_max_cap, v.odometer as vehicle_odometer,

               d.name as driver_name, d.phone as driver_phone, d.license_category as driver_category

        FROM trips t

        JOIN vehicles v ON t.vehicle_id = v.id

        JOIN drivers d ON t.driver_id = d.id

        ORDER BY t.id DESC

    ''').fetchall()



    available_vehicles = conn.execute("SELECT * FROM vehicles WHERE status = 'Available'").fetchall()

    available_drivers = conn.execute("SELECT * FROM drivers WHERE status = 'On Duty'").fetchall()

    conn.close()



    return render_template(

        'trips.html',

        trips=trips_list,

        available_vehicles=available_vehicles,

        available_drivers=available_drivers

    )



@app.route('/trips/create', methods=['POST'])

@login_required

@role_required('Manager', 'Dispatcher')

def create_trip():

    vehicle_id = int(request.form.get('vehicle_id'))

    driver_id = int(request.form.get('driver_id'))

    cargo_weight = float(request.form.get('cargo_weight', 0))

    revenue = float(request.form.get('revenue', 0))

    cargo_description = request.form.get('cargo_description', '').strip()

    origin = request.form.get('origin', '').strip()

    destination = request.form.get('destination', '').strip()

    action = request.form.get('action', 'draft')



    conn = get_db()

    vehicle = conn.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()

    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()



    if not vehicle or not driver:

        conn.close()

        flash('Invalid vehicle or driver selected.', 'danger')

        return redirect(url_for('trips'))



    # Validation Rule 1: Prevent trip creation if CargoWeight > MaxCapacity

    if cargo_weight > vehicle['max_capacity']:

        conn.close()

        flash(f'Validation Error: Cargo weight ({cargo_weight} kg) exceeds vehicle max capacity ({vehicle["max_capacity"]} kg). Trip creation blocked.', 'danger')

        return redirect(url_for('trips'))



    # Validation Rule 2: Driver license compliance check

    try:

        exp_date = datetime.strptime(str(driver['license_expiry'])[:10], '%Y-%m-%d').date()

        if exp_date < date.today():

            conn.close()

            flash(f'Validation Error: Driver {driver["name"]} has an EXPIRED license. Assignment blocked.', 'danger')

            return redirect(url_for('trips'))

    except Exception:

        pass



    # Validation Rule 3: Category match

    if driver['license_category'] != 'All' and driver['license_category'] != vehicle['type']:

        conn.close()

        flash(f'Validation Error: Driver {driver["name"]} has category "{driver["license_category"]}" but vehicle is "{vehicle["type"]}". Assignment blocked.', 'danger')

        return redirect(url_for('trips'))



    status = 'Dispatched' if action == 'dispatch' else 'Draft'

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Dispatched' else None



    cursor = conn.cursor()

    cursor.execute('''

        INSERT INTO trips (vehicle_id, driver_id, cargo_weight, cargo_description, origin, destination, status, revenue, start_odometer, start_time, created_by)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    ''', (vehicle_id, driver_id, cargo_weight, cargo_description, origin, destination, status, revenue, vehicle['odometer'], start_time, current_user.id))



    if status == 'Dispatched':

        cursor.execute("UPDATE vehicles SET status = 'On Trip' WHERE id = ?", (vehicle_id,))

        cursor.execute("UPDATE drivers SET status = 'On Trip' WHERE id = ?", (driver_id,))



    conn.commit()

    conn.close()



    flash(f'Trip {"dispatched" if status=="Dispatched" else "saved as Draft"} successfully!', 'success')

    return redirect(url_for('trips'))



@app.route('/trips/<int:trip_id>/dispatch', methods=['POST'])

@login_required

@role_required('Manager', 'Dispatcher')

def dispatch_trip(trip_id):

    conn = get_db()

    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()

    if trip:

        vehicle = conn.execute('SELECT * FROM vehicles WHERE id = ?', (trip['vehicle_id'],)).fetchone()

        driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (trip['driver_id'],)).fetchone()



        if vehicle['status'] != 'Available':

            flash(f'Cannot dispatch: Vehicle is currently "{vehicle["status"]}".', 'danger')

        elif driver['status'] != 'On Duty':

            flash(f'Cannot dispatch: Driver is currently "{driver["status"]}".', 'danger')

        else:

            conn.execute('''

                UPDATE trips 

                SET status = 'Dispatched', start_time = CURRENT_TIMESTAMP, start_odometer = ? 

                WHERE id = ?

            ''', (vehicle['odometer'], trip_id))

            conn.execute("UPDATE vehicles SET status = 'On Trip' WHERE id = ?", (trip['vehicle_id'],))

            conn.execute("UPDATE drivers SET status = 'On Trip' WHERE id = ?", (trip['driver_id'],))

            conn.commit()

            flash(f'Trip #TRIP-{trip_id} dispatched! Vehicle & Driver set to "On Trip".', 'success')

    conn.close()

    return redirect(url_for('trips'))



@app.route('/trips/<int:trip_id>/complete', methods=['POST'])

@login_required

def complete_trip(trip_id):

    final_odometer = int(request.form.get('final_odometer', 0))

    conn = get_db()

    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()



    if trip:

        start_odo = trip['start_odometer'] or 0

        if final_odometer < start_odo:

            flash(f'Error: Final odometer ({final_odometer} km) cannot be less than starting odometer ({start_odo} km).', 'danger')

            conn.close()

            return redirect(url_for('trips'))



        distance = final_odometer - start_odo



        conn.execute('''

            UPDATE trips 

            SET status = 'Completed', end_odometer = ?, distance = ?, end_time = CURRENT_TIMESTAMP 

            WHERE id = ?

        ''', (final_odometer, distance, trip_id))



        conn.execute("UPDATE vehicles SET status = 'Available', odometer = ? WHERE id = ?", (final_odometer, trip['vehicle_id']))

        conn.execute("UPDATE drivers SET status = 'On Duty', trips_completed = trips_completed + 1 WHERE id = ?", (trip['driver_id'],))

        conn.commit()



        flash(f'Trip #TRIP-{trip_id} completed successfully! Distance: {distance} km. Vehicle & Driver returned to Available.', 'success')



    conn.close()

    return redirect(url_for('trips'))



@app.route('/trips/<int:trip_id>/cancel', methods=['POST'])

@login_required

@role_required('Manager', 'Dispatcher')

def cancel_trip(trip_id):

    conn = get_db()

    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()

    if trip:

        if trip['status'] == 'Dispatched':

            conn.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (trip['vehicle_id'],))

            conn.execute("UPDATE drivers SET status = 'On Duty' WHERE id = ?", (trip['driver_id'],))



        conn.execute("UPDATE trips SET status = 'Cancelled' WHERE id = ?", (trip_id,))

        conn.commit()

        flash(f'Trip #TRIP-{trip_id} cancelled.', 'info')

    conn.close()

    return redirect(url_for('trips'))



# -------------------------------------------------------------

# PAGE 5: MAINTENANCE & SERVICE LOGS

# -------------------------------------------------------------



@app.route('/maintenance')

@login_required

def maintenance():

    conn = get_db()

    logs = conn.execute('''

        SELECT m.*, v.name as vehicle_name, v.license_plate

        FROM maintenance m

        JOIN vehicles v ON m.vehicle_id = v.id

        ORDER BY m.id DESC

    ''').fetchall()



    all_vehicles = conn.execute("SELECT * FROM vehicles ORDER BY name ASC").fetchall()

    conn.close()



    return render_template('maintenance.html', maintenance_logs=logs, all_vehicles=all_vehicles)



@app.route('/maintenance/add', methods=['POST'])

@login_required

@role_required('Manager')

def add_maintenance():

    vehicle_id = int(request.form.get('vehicle_id'))

    service_type = request.form.get('service_type', '').strip()

    description = request.form.get('description', '').strip()

    service_date = request.form.get('service_date')

    cost = float(request.form.get('cost', 0))

    vendor = request.form.get('vendor', '').strip()

    next_service_date = request.form.get('next_service_date') or None



    conn = get_db()

    conn.execute('''

        INSERT INTO maintenance (vehicle_id, service_date, service_type, description, cost, vendor, status, next_service_date, created_by)

        VALUES (?, ?, ?, ?, ?, ?, 'In Progress', ?, ?)

    ''', (vehicle_id, service_date, service_type, description, cost, vendor, next_service_date, current_user.id))



    # Auto-Logic: Switch vehicle status to "In Shop"

    conn.execute("UPDATE vehicles SET status = 'In Shop' WHERE id = ?", (vehicle_id,))

    conn.commit()

    conn.close()



    flash('Maintenance logged. Vehicle automatically set to "In Shop" and removed from dispatch pool.', 'warning')

    return redirect(url_for('maintenance'))



@app.route('/maintenance/<int:maintenance_id>/complete', methods=['POST'])

@login_required

@role_required('Manager')

def complete_maintenance(maintenance_id):

    conn = get_db()

    log = conn.execute('SELECT * FROM maintenance WHERE id = ?', (maintenance_id,)).fetchone()

    if log:

        conn.execute("UPDATE maintenance SET status = 'Completed' WHERE id = ?", (maintenance_id,))

        conn.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (log['vehicle_id'],))

        conn.commit()

        flash('Service marked completed. Vehicle restored to "Available" pool.', 'success')

    conn.close()

    return redirect(url_for('maintenance'))



# -------------------------------------------------------------

# PAGE 6: FUEL & EXPENSES

# -------------------------------------------------------------



@app.route('/expenses')

@login_required

def expenses():

    conn = get_db()

    fuel_logs = conn.execute('''

        SELECT f.*, v.name as vehicle_name, v.license_plate

        FROM fuel_logs f

        JOIN vehicles v ON f.vehicle_id = v.id

        ORDER BY f.id DESC

    ''').fetchall()



    expenses_list = conn.execute('''

        SELECT e.*, v.name as vehicle_name, v.license_plate

        FROM expenses e

        JOIN vehicles v ON e.vehicle_id = v.id

        ORDER BY e.id DESC

    ''').fetchall()



    total_fuel_cost = conn.execute("SELECT COALESCE(SUM(cost), 0) as s FROM fuel_logs").fetchone()['s']

    total_fuel_liters = conn.execute("SELECT COALESCE(SUM(liters), 0) as s FROM fuel_logs").fetchone()['s']

    total_maintenance_cost = conn.execute("SELECT COALESCE(SUM(cost), 0) as s FROM maintenance").fetchone()['s']

    total_other_expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) as s FROM expenses").fetchone()['s']

    total_operational_cost = total_fuel_cost + total_maintenance_cost + total_other_expenses



    all_vehicles = conn.execute("SELECT * FROM vehicles WHERE status != 'Retired' ORDER BY name ASC").fetchall()

    recent_trips = conn.execute("SELECT id, origin, destination FROM trips ORDER BY id DESC LIMIT 15").fetchall()

    conn.close()



    return render_template(

        'expenses.html',

        fuel_logs=fuel_logs,

        expenses=expenses_list,

        total_fuel_cost=total_fuel_cost,

        total_fuel_liters=total_fuel_liters,

        total_maintenance_cost=total_maintenance_cost,

        total_other_expenses=total_other_expenses,

        total_operational_cost=total_operational_cost,

        all_vehicles=all_vehicles,

        recent_trips=recent_trips

    )



@app.route('/fuel/add', methods=['POST'])

@login_required

def add_fuel():

    vehicle_id = int(request.form.get('vehicle_id'))

    trip_id = int(request.form.get('trip_id')) if request.form.get('trip_id') else None

    liters = float(request.form.get('liters', 0))

    cost = float(request.form.get('cost', 0))

    odometer = int(request.form.get('odometer', 0))

    fuel_date = request.form.get('fuel_date')



    conn = get_db()

    conn.execute('''

        INSERT INTO fuel_logs (vehicle_id, trip_id, liters, cost, odometer, fuel_date)

        VALUES (?, ?, ?, ?, ?, ?)

    ''', (vehicle_id, trip_id, liters, cost, odometer, fuel_date))



    conn.execute("UPDATE vehicles SET odometer = MAX(odometer, ?) WHERE id = ?", (odometer, vehicle_id))

    conn.commit()

    conn.close()



    flash(f'Recorded {liters}L fuel refill (${cost:.2f}).', 'success')

    return redirect(url_for('expenses'))



@app.route('/expenses/add', methods=['POST'])

@login_required

def add_expense():

    vehicle_id = int(request.form.get('vehicle_id'))

    trip_id = int(request.form.get('trip_id')) if request.form.get('trip_id') else None

    expense_type = request.form.get('expense_type')

    amount = float(request.form.get('amount', 0))

    description = request.form.get('description', '').strip()

    expense_date = request.form.get('expense_date')



    conn = get_db()

    conn.execute('''

        INSERT INTO expenses (vehicle_id, trip_id, expense_type, amount, description, expense_date)

        VALUES (?, ?, ?, ?, ?, ?)

    ''', (vehicle_id, trip_id, expense_type, amount, description, expense_date))

    conn.commit()

    conn.close()



    flash(f'Expense "{expense_type}" (${amount:.2f}) logged.', 'success')

    return redirect(url_for('expenses'))



# -------------------------------------------------------------

# PAGE 7: DRIVER PERFORMANCE & SAFETY PROFILES

# -------------------------------------------------------------



@app.route('/drivers')

@login_required

def drivers():

    conn = get_db()

    drivers_list = conn.execute("SELECT * FROM drivers ORDER BY id DESC").fetchall()

    conn.close()

    return render_template('drivers.html', drivers=drivers_list)



@app.route('/drivers/add', methods=['POST'])

@login_required

@role_required('Manager', 'Safety Officer')

def add_driver():

    name = request.form.get('name', '').strip()

    license_number = request.form.get('license_number', '').strip().upper()

    license_category = request.form.get('license_category')

    license_expiry = request.form.get('license_expiry')

    phone = request.form.get('phone', '').strip()

    safety_score = int(request.form.get('safety_score', 100))



    conn = get_db()

    try:

        conn.execute('''

            INSERT INTO drivers (name, license_number, license_category, license_expiry, phone, safety_score, status)

            VALUES (?, ?, ?, ?, ?, ?, 'On Duty')

        ''', (name, license_number, license_category, license_expiry, phone, safety_score))

        conn.commit()

        flash(f'Driver "{name}" onboarded successfully.', 'success')

    except Exception as e:

        flash(f'Error adding driver: License number must be unique ({e}).', 'danger')

    finally:

        conn.close()



    return redirect(url_for('drivers'))



@app.route('/drivers/<int:driver_id>/toggle-status', methods=['POST'])

@login_required

@role_required('Manager', 'Safety Officer')

def toggle_driver_status(driver_id):

    new_status = request.form.get('new_status')

    conn = get_db()

    conn.execute("UPDATE drivers SET status = ? WHERE id = ?", (new_status, driver_id))

    conn.commit()

    conn.close()

    flash(f'Driver duty status changed to "{new_status}".', 'info')

    return redirect(url_for('drivers'))



# -------------------------------------------------------------

# PAGE 8: OPERATIONAL ANALYTICS & FINANCIAL REPORTS

# -------------------------------------------------------------



@app.route('/reports')

@login_required

def reports():

    conn = get_db()



    vehicles_data = conn.execute('''

        SELECT 

            v.id, v.name, v.model, v.license_plate, v.type, v.acquisition_cost, v.odometer,

            COALESCE((SELECT SUM(revenue) FROM trips WHERE vehicle_id = v.id AND status = 'Completed'), 0) as total_revenue,

            COALESCE((SELECT SUM(cost) FROM fuel_logs WHERE vehicle_id = v.id), 0) as total_fuel,

            COALESCE((SELECT SUM(liters) FROM fuel_logs WHERE vehicle_id = v.id), 0) as total_liters,

            COALESCE((SELECT SUM(cost) FROM maintenance WHERE vehicle_id = v.id), 0) as total_maintenance,

            COALESCE((SELECT SUM(amount) FROM expenses WHERE vehicle_id = v.id), 0) as total_expenses

        FROM vehicles v

    ''').fetchall()



    roi_data = []

    efficiency_data = []



    for v in vehicles_data:

        net_profit = v['total_revenue'] - (v['total_fuel'] + v['total_maintenance'] + v['total_expenses'])

        acq_cost = v['acquisition_cost']

        roi_pct = round((net_profit / acq_cost) * 100, 2) if acq_cost > 0 else 0



        roi_data.append({

            'name': v['name'],

            'license_plate': v['license_plate'],

            'type': v['type'],

            'acquisition_cost': acq_cost,

            'total_revenue': v['total_revenue'],

            'total_fuel': v['total_fuel'],

            'total_maintenance': v['total_maintenance'],

            'total_expenses': v['total_expenses'],

            'net_profit': net_profit,

            'roi_percentage': roi_pct

        })



        fuel_eff = round(v['odometer'] / v['total_liters'], 2) if v['total_liters'] > 0 else 0

        total_op_cost = v['total_fuel'] + v['total_maintenance'] + v['total_expenses']

        cost_per_km = round(total_op_cost / v['odometer'], 2) if v['odometer'] > 0 else 0



        efficiency_data.append({

            'name': v['name'],

            'license_plate': v['license_plate'],

            'odometer': v['odometer'],

            'total_liters': v['total_liters'],

            'fuel_efficiency': fuel_eff,

            'total_operating_cost': total_op_cost,

            'cost_per_km': cost_per_km

        })



    conn.close()

    return render_template('reports.html', roi_data=roi_data, efficiency_data=efficiency_data)



@app.route('/reports/export/<report_type>')

@login_required

@role_required('Manager', 'Financial Analyst')

def export_csv(report_type):

    conn = get_db()

    si = StringIO()

    cw = csv.writer(si)



    if report_type == 'fuel':

        rows = conn.execute('''

            SELECT f.id, v.name as Vehicle, v.license_plate as Plate, f.liters as Liters, f.cost as Cost, f.odometer as Odometer, f.fuel_date as Date

            FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.id ORDER BY f.fuel_date DESC

        ''').fetchall()

        filename = 'fleetflow_fuel_report.csv'

    elif report_type == 'maintenance':

        rows = conn.execute('''

            SELECT m.id, v.name as Vehicle, v.license_plate as Plate, m.service_type as Service, m.cost as Cost, m.vendor as Vendor, m.status as Status, m.service_date as Date

            FROM maintenance m JOIN vehicles v ON m.vehicle_id = v.id ORDER BY m.service_date DESC

        ''').fetchall()

        filename = 'fleetflow_maintenance_report.csv'

    else:

        rows = conn.execute('''

            SELECT t.id as TripID, v.name as Vehicle, d.name as Driver, t.origin as Origin, t.destination as Destination, t.cargo_weight as Payload_kg, t.distance as Distance_km, t.revenue as Revenue, t.status as Status

            FROM trips t JOIN vehicles v ON t.vehicle_id = v.id JOIN drivers d ON t.driver_id = d.id ORDER BY t.id DESC

        ''').fetchall()

        filename = 'fleetflow_financial_trips_report.csv'



    conn.close()



    if rows:

        cw.writerow([k for k in rows[0].keys()])

        for r in rows:

            cw.writerow(list(r))



    output = make_response(si.getvalue())

    output.headers["Content-Disposition"] = f"attachment; filename={filename}"

    output.headers["Content-type"] = "text/csv"

    return output



if __name__ == '__main__':

    init_db()

    seed_data()

    print("FleetFlow Master OS running on http://127.0.0.1:5000")

    app.run(debug=True, port=5000)

