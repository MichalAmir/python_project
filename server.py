import os
from flask import Flask, render_template, request, url_for, redirect, session as flask_session, jsonify, flash
from werkzeug.security import check_password_hash
from database import update_doctor, delete_doctor, add_doctor, doctors, session as db_session, get_user_by_username, get_user_by_email, add_user, add_appointment, get_appointments
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # חשוב להגדיר SECRET_KEY

# הגדרת תיקייה להעלאת קבצים
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# הגדרת רמות הלוגים
logging.basicConfig(level=logging.DEBUG)

# פונקציה לבדוק אם הסיומת מותרת
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    doctors_list = db_session.query(doctors).all()  # מחזיר את כל הרופאים מהטבלה
    return render_template("index.html", doctors=doctors_list)  # מעביר את הרשימה לעמוד

# פונקציה חדשה להזמנת פגישה
@app.route("/book", methods=["POST"])
def book():
    client_name = request.form.get("name")
    doctor_name = request.form.get("doctor_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    date = request.form.get("date")
    message = request.form.get("message")

    # הוספת הפגישה למסד הנתונים
    add_appointment(client_name, doctor_name, email, phone, date, message)

    # החזרת תגובה ב-JSON במקום הפנייה מחדש
    return jsonify({"message": "The session was successfully saved"})


# תצוגת פרטי רופא לפי ה-ID
@app.route("/doctor1/<int:doctor_id>")
def doctor1(doctor_id):
    # כאן תוכל להוסיף קוד כדי לאחזר את פרטי הרופא מהדאטהבייס בעזרת ה-ID
    doctor = db_session.query(doctors).filter(doctors.c.dr_id == doctor_id).first()
    if not doctor:
        return "Doctor not found", 404  # החזר 404 אם הרופא לא נמצא
    return render_template("doctor1.html", doctor=doctor)


# הוספת רופא
@app.route("/add_doctor", methods=["GET", "POST"])
def add_new_doctor():
    if request.method == "POST":
        name = request.form["name"]
        seniority = request.form["seniority"]
        age = request.form["age"]
        category = request.form["category"]
        image_url = request.form["image_url"]  # קבלת ה-URL מהשדה
        description = request.form["description"]  # קבלת התיאור מהשדה

        # הוספת רופא למסד הנתונים
        add_doctor(name, seniority, age, category, image_url, description)
        return redirect(url_for("admin_page"))  # הפנייה לעמוד הניהול
    return render_template("add_doctor.html")

# מחיקת רופא
@app.route("/delete_doctor/<int:doctor_id>", methods=["POST"])
def delete_doctor_route(doctor_id):
    delete_doctor(doctor_id)  # קריאה לפונקציה למחיקת רופא
    return redirect(url_for("admin_page"))  # הפנה לעמוד הניהול

# עריכת רופא
@app.route("/edit_doctor/<int:doctor_id>", methods=["GET", "POST"])
def edit_doctor_route(doctor_id):
    doctor = db_session.query(doctors).filter(doctors.c.dr_id == doctor_id).first()  # מציאת הרופא
    if request.method == "POST":
        name = request.form["name"]
        seniority = request.form["seniority"]
        age = request.form["age"]
        category = request.form["category"]
        image_url = request.form["image_url"]  # עדכון ה-URL שנכנס מהטופס
        description = request.form["description"]  # עדכון התיאור מהשדה

        update_doctor(doctor_id, name, seniority, age, category, image_url, description)  # עדכון הרופא במסד הנתונים
        return redirect(url_for("admin_page"))  # הפנייה לעמוד הניהול
    return render_template("edit_doctor.html", doctor=doctor)  # מעביר את פרטי הרופא לתבנית


@app.route("/admin")
def admin_page():
    if flask_session.get("is_admin"):
        doctors_list = db_session.query(doctors).all()
        appointments_list = get_appointments()  # Retrieve the list of appointments
        return render_template("admin.html", doctors=doctors_list, appointments=appointments_list)  # Pass appointments to the template
    else:
        return redirect(url_for("login"))

# התחברות
@app.route("/login", methods=["GET", "POST"])
def login():
    username_error = False  # Initialize the variable
    password_error = False  # Initialize the variable

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check for admin credentials (unchanged)
        if username == "admin" and password == "123456":
            flask_session["is_admin"] = True
            return redirect(url_for("admin_page"))

        # Check for regular users
        user = get_user_by_username(username)
        if user:  # Username found
            if not check_password_hash(user.password, password):  # Only check password if username is valid
                password_error = True
            else:  # Correct password
                flask_session["user_id"] = user.id
                return redirect(url_for("index"))
        else:  # Username not found
            username_error = True  # Set username_error here
            username = ""  # Set username to an empty string if not found

        return render_template("login.html", username=username, username_error=username_error,
                               password_error=password_error)

    # If the request is GET (initial page load)
    return render_template("login.html", username_error=username_error, password_error=password_error)

# רישום משתמש חדש
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # מקבל את הערכים מהטופס של המשתמש
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        # בודק אם המשתמש כבר קיים
        existing_user = get_user_by_username(username)
        if existing_user:
            flash("Username already exists", "error")
            return redirect(url_for("register"))

        # בודק אם האימייל כבר קיים
        existing_email = get_user_by_email(email)
        if existing_email:
            flash("Email already exists", "error")
            return redirect(url_for("register"))

        # מוסיף משתמש חדש
        add_user(username, password, email)
        flash("Registration successful", "success")
        return redirect(url_for("index"))

    # אם השיטה היא GET, מציג את טופס ההרשמה
    return render_template("register.html")

@app.route("/some_route", methods=["GET", "POST"])
def some_route():
    doctors_list = db_session.query(doctors).all()  # שליפת כל הרופאים מהדאטהבייס
    if request.method == "POST":
        # כאן יהיה הקוד שמטפל בטופס
        selected_doctor_id = request.form.get("doctor")
        # תוכל להשתמש ב-selected_doctor_id להמשך טיפול

    return render_template("some_template.html", doctors=doctors_list)

port_number = 3000
if __name__ == '__main__':
    app.run(port=port_number)

