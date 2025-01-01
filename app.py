from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from datetime import timedelta
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
import os
from functools import wraps
import news

app = Flask(__name__)

# Secret key for session management (should be kept secret in a real application)
app.secret_key = 'your_secret_key'

# Directory to save uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(HTTPException)
def handle_exception(e):
    # Handle HTTP exceptions
    return render_template('apology.html', error_message=str(e)), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    # Handle non-HTTP exceptions only
    return render_template('apology.html', error_message=str(e)), 500

@app.route('/')
def index():
    # Retrieve the username from the session
    username = session.get('username', 'Guest')
    # Render the index.html template with the username
    return render_template('index.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validate the username and password with the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'login_error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer']
        
        # Check if password and confirm password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'register_error')
            return render_template('register.html')
        
        # Hash the password and security answer
        hashed_password = generate_password_hash(password)
        hashed_security_answer = generate_password_hash(security_answer)
        
        # Save the user information in the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password, email, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_password, email, security_question, hashed_security_answer))
        db.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if 'retrieve_question' in request.form:
            username = request.form['username']
            # Retrieve the security question from the database
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT security_question FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                security_question = user[0]
                return render_template('forgot_password.html', username=username, security_question=security_question)
            else:
                flash('Username not found. Please try again.', 'forgot_password_error')
        elif 'reset_password' in request.form:
            username = request.form['username']
            security_answer = request.form['security_answer']
            new_password = request.form['new_password']
            # Retrieve the security answer from the database
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT security_answer FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[0], security_answer):
                # Hash the new password
                hashed_new_password = generate_password_hash(new_password)
                # Update the password in the database
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_new_password, username))
                db.commit()
                flash('Password reset successful. Please log in with your new password.', 'forgot_password_success')
                return redirect(url_for('login'))
            else:
                flash('Incorrect security answer. Please try again.', 'forgot_password_error')
    return render_template('forgot_password.html')

@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        body = request.form['body']
        image = request.files['image']
        author = session['username']
        
        if not title or not description or not body:
            return 'Missing data', 400
        
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
        else:
            image_url = None
        
        news.add_article(title, description, body, image_url, author)
        return redirect(url_for('news_list'))
    return render_template('add_news.html')

@app.route('/news')
def news_list():
    articles = news.get_all_articles()
    return render_template('news_list.html', articles=articles)

@app.route('/shop')
def shop():
    # Render the shop.html template
    return render_template('shop.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    username = session.get('username')
    # Add logic to delete the account from the database
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        # Add logic to change the password
        return redirect(url_for('settings'))
    return render_template('change_password.html')

@app.route('/change_username', methods=['GET', 'POST'])
@login_required
def change_username():
    if request.method == 'POST':
        # Add logic to change the username
        return redirect(url_for('settings'))
    return render_template('change_username.html')

@app.route('/change_cellphone', methods=['GET', 'POST'])
@login_required
def change_cellphone():
    if request.method == 'POST':
        # Add logic to change the cellphone number
        return redirect(url_for('settings'))
    return render_template('change_cellphone.html')

@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        # Add logic to change the email
        return redirect(url_for('settings'))
    return render_template('change_email.html')

@app.route('/data_analyzer')
def data_analyzer():
    # Render the data_analyzer.html template
    return render_template('data_analyzer.html')

@app.route('/game')
def game():
    # Render the game.html template
    games = [
        {"title": "Game 1", "description": "Description for game 1"},
        {"title": "Game 2", "description": "Description for game 2"}
    ]
    return render_template('game.html', games=games)

# Set session lifetime to 7 days
app.permanent_session_lifetime = timedelta(days=7)

# Database file path
DATABASE = 'website.db'

# Function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Ensure the upload folder exists
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Decorator to require login for certain routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(HTTPException)
def handle_exception(e):
    # Handle HTTP exceptions
    return render_template('apology.html', error_message=str(e)), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    # Handle non-HTTP exceptions only
    return render_template('apology.html', error_message=str(e)), 500

@app.route('/')
def index():
    # Retrieve the username from the session
    username = session.get('username', 'Guest')
    # Render the index.html template with the username
    return render_template('index.html', username=username)

@app.route('/news')
def news_list():
    articles = news.get_all_articles()
    return render_template('news_list.html', articles=articles)

@app.route('/game')
def game():
    games = [
        {"title": "Game 1", "description": "Description for game 1"},
        {"title": "Game 2", "description": "Description for game 2"}
    ]
    return render_template('game.html', games=games)

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/data_analyzer')
def data_analyzer():
    return render_template('data_analyzer.html')

@app.route('/recreational_activities')
def recreational_activities():
    activities = [
        {"title": "Activity 1", "description": "Description for activity 1"},
        {"title": "Activity 2", "description": "Description for activity 2"}
    ]
    return render_template('recreational_activities.html', activities=activities)

@app.route('/blogs')
def blogs():
    blogs = [
        {"title": "Blog 1", "description": "Description for blog 1"},
        {"title": "Blog 2", "description": "Description for blog 2"}
    ]
    return render_template('blogs.html', blogs=blogs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'login_error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer']
        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'register_error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        hashed_security_answer = generate_password_hash(security_answer)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password, email, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_password, email, security_question, hashed_security_answer))
        db.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if 'retrieve_question' in request.form:
            username = request.form['username']
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT security_question FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                security_question = user[0]
                return render_template('forgot_password.html', username=username, security_question=security_question)
            else:
                flash('Username not found. Please try again.', 'forgot_password_error')
        elif 'reset_password' in request.form:
            username = request.form['username']
            security_answer = request.form['security_answer']
            new_password = request.form['new_password']
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT security_answer FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[0], security_answer):
                hashed_new_password = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_new_password, username))
                db.commit()
                flash('Password reset successful. Please log in with your new password.', 'forgot_password_success')
                return redirect(url_for('login'))
            else:
                flash('Incorrect security answer. Please try again.', 'forgot_password_error')
    return render_template('forgot_password.html')

@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        body = request.form['body']
        image = request.files['image']
        author = session['username']
        
        if not title or not description or not body:
            return 'Missing data', 400
        
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
        else:
            image_url = None
        
        news.add_article(title, description, body, image_url, author)
        return redirect(url_for('news_list'))
    return render_template('add_news.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    username = session.get('username')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    db.commit()
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (session['username'],))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[0], current_password):
            if new_password == confirm_new_password:
                hashed_new_password = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_new_password, session['username']))
                db.commit()
                flash('Password changed successfully.', 'settings_success')
            else:
                flash('New passwords do not match. Please try again.', 'settings_error')
        else:
            flash('Current password is incorrect. Please try again.', 'settings_error')
        
        return redirect(url_for('settings'))
    return render_template('change_password.html')

@app.route('/change_username', methods=['GET', 'POST'])
@login_required
def change_username():
    if request.method == 'POST':
        new_username = request.form['new_username']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, session['username']))
        db.commit()
        session['username'] = new_username
        flash('Username changed successfully.', 'settings_success')
        
        return redirect(url_for('settings'))
    return render_template('change_username.html')

@app.route('/change_cellphone', methods=['GET', 'POST'])
@login_required
def change_cellphone():
    if request.method == 'POST':
        new_cellphone = request.form['new_cellphone']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET cellphone = ? WHERE username = ?", (new_cellphone, session['username']))
        db.commit()
        flash('Cellphone number changed successfully.', 'settings_success')
        
        return redirect(url_for('settings'))
    return render_template('change_cellphone.html')

@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form['new_email']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, session['username']))
        db.commit()
        flash('Email changed successfully.', 'settings_success')
        
        return redirect(url_for('settings'))
    return render_template('change_email.html')

# Set session lifetime to 7 days
app.permanent_session_lifetime = timedelta(days=7)

if __name__ == '__main__':
    news.init_db()  # Initialize the database
    app.run(debug=True, port=5001)