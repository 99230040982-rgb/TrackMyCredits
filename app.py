from flask import Flask, request, render_template, redirect, url_for, flash, session,jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import webbrowser
import threading
import smtplib
# === Flask App Config ===
app = Flask(__name__)
app.secret_key = 'Hello'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "TrackMyCredits.db")

# === Initialize Database ===
def init_db():
    print("🔧 Initializing database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # === USERS TABLE ===
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # === COURSES TABLE ===
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            grade TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            batch TEXT,
            branch TEXT,
            email TEXT,
            contact TEXT,
            feedback TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    # === Verify columns exist (auto-upgrade if needed) ===
    c.execute("PRAGMA table_info(courses)")
    existing_columns = [col[1] for col in c.fetchall()]
    if "category" not in existing_columns:
        print("🛠 Adding missing column: category")
        c.execute("ALTER TABLE courses ADD COLUMN category TEXT DEFAULT 'unknown'")
        conn.commit()

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully at:", DB_PATH)

def send_email(recipient):
    sender = "trackmycredits.devteam@gmail.com"  
    password = "hpsm vznm npno waat"        
    subject = f"Welcome to Track My Credits – Registration Successful!"
    message = (f"Hello {recipient},\n\n"
               f"Thank you for registering with Track My Credits.\n"
               f"Your account has been successfully created, and you can now log in to track your academic credits\n and understand the credit system at Kalasalingam University.\n"
               f"If you have any questions or need help, feel free to reach out to us using the our website.\n")
    email_message = f"Subject: {subject}\n\n{message}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, email_message)
        print(f"Notification sent to {recipient}")
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")

# === Helper Function: Fetch Courses by User ===
def get_courses(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT category, course_name, credits, grade FROM courses WHERE username = ?", (username,))
    courses = c.fetchall()
    conn.close()

    course_dict = {}
    for category, name, credits, grade in courses:
        if category not in course_dict:
            course_dict[category] = []
        course_dict[category].append({
            "name": name,
            "credits": credits,
            "grade": grade
        })
    return course_dict


# === ROUTES ===
@app.route('/')
def Home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact',methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        batch = request.form.get('batch')
        branch = request.form.get('branch')
        email = request.form.get('email')
        contact = request.form.get('contact')
        feedback = request.form.get('feedback')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO contact_messages (name, batch, branch, email, contact, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, batch, branch, email, contact, feedback))
        conn.commit()
        conn.close()
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()

        if '_flashes' in session:
            session.pop('_flashes')

        if result and check_password_hash(result[0], password):
            session['user'] = username
            return redirect(url_for('personalized'))
        else:
            flash("❌ Incorrect email or password.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if '_flashes' in session:
        session.pop('_flashes')

    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            send_email(username)
            flash("✅ Registration successful! Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("⚠️ User already exists.")
            return redirect(url_for('register'))

    return render_template('register.html')
# === 8 Credit Categories ===
CATEGORIES = [
    {"code": "ec", "title": "Experiential Core", "description": "Hands-on learning bridging theory and practice.", "total": 16},
    {"code": "ee", "title": "Experiential Electives", "description": "Tailored experiential opportunities.", "total": 8},
    {"code": "fc", "title": "Foundation Core", "description": "Essential foundational knowledge.", "total": 44},
    {"code": "ho", "title": "Honours", "description": "Advanced academic work for high achievers.(OPTIONAL)", "total": 20},
    {"code": "mi", "title": "Minors", "description": "Concentrated study in another field.(OPTIONAL)", "total": 20},
    {"code": "pc", "title": "Program Core", "description": "Core courses specific to your major.", "total": 52},
    {"code": "pe", "title": "Program Electives", "description": "Specialized courses within your major.", "total": 24},
    {"code": "ue", "title": "University Electives", "description": "Free elective courses from any department.", "total": 16}
]


@app.route('/personalized')
def personalized():
    if 'user' not in session:
        flash("⚠️ Please log in first.")
        return redirect(url_for('login'))

    username = session['user']
    course_dict = get_courses(username)
    for cat in CATEGORIES:
        code = cat['code']
        cat['earned'] = sum([c['credits'] for c in course_dict.get(code, [])])
        cat['remaining'] = cat['total'] - cat['earned']
        cat['percent'] = round((cat['earned'] / cat['total']) * 100) if cat['total'] > 0 else 0

    total_earned = sum(c['earned'] for c in CATEGORIES)
    total_possible = sum(c['total'] for c in CATEGORIES)
    percent_complete = round((total_earned / total_possible) * 100)

    return render_template(
        'personalized.html',
        username=username,
        categories=CATEGORIES,
        course_dict=course_dict,
        total_credits_earned=total_earned,
        total_credits_remaining=total_possible - total_earned,
        percentage_complete=percent_complete
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('Home'))

@app.route('/add_course', methods=['POST'])
def add_course():
    if 'user' not in session:
        flash("⚠️ Please log in first.")
        return redirect(url_for('login'))

    username = session['user']
    category = request.form.get('category_code')   # ✅ Corrected field name
    course_name = request.form.get('course_name')
    credits = request.form.get('course_credits')   # ✅ Matches HTML field
    grade = request.form.get('course_grade')       # ✅ Matches HTML field

    if not all([category, course_name, credits]):
        flash("⚠️ Please fill out all required fields.")
        return redirect(url_for('personalized'))

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO courses (username, category, course_name, credits, grade)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, category, course_name, credits, grade))
        conn.commit()
        conn.close()
    except Exception as e:
        print("❌ Database insert error:", e)
        flash("⚠️ Something went wrong while saving your course.")

    return redirect(url_for('personalized'))
@app.route('/delete_course', methods=['POST'])
def delete_course():
    if 'user' not in session:
        return jsonify({"success": False, "error": "Not logged in"})

    data = request.get_json(force=True)  # <— ensures JSON is parsed
    username = session['user']
    category = data.get('category')
    course_name = data.get('course_name')

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM courses WHERE username = ? AND category = ? AND course_name = ?",
                  (username, category, course_name))
        conn.commit()
        conn.close()

        print(f"✅ Deleted course: {course_name} ({category}) for {username}")
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Error deleting course: {e}")
        return jsonify({"success": False, "error": str(e)})

# === MAIN APP ENTRY ===
if __name__ == '__main__':
    init_db()
    webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True)
