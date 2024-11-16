from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Date, select, Boolean
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# הגדרת מחרוזת החיבור
DATABASE_URI = 'mssql+pyodbc://@DESKTOP-24EQMFH/python_data?driver=SQL+Server&Trusted_Connection=yes'

engine = create_engine(DATABASE_URI)


Session = sessionmaker(bind=engine)
session = Session()

# הגדרת האובייקט שמכיל את כל מבני הטבלאות
metadata = MetaData()

# טבלת הרופאים כולל עמודת התמונה
doctors = Table('doctors', metadata,
                Column('dr_id', Integer, primary_key=True),
                Column('dr_name', String(50), nullable=False),
                Column('dr_seniority', Integer),
                Column('dr_age', Integer),
                Column('dr_category', String(50)),
                Column('dr_image_url', String(255)),  # עמודה לתמונה
                Column('dr_description', Text))  # עמודה לתיאור הרופא

users = Table('users', metadata,
              Column('id', Integer, primary_key=True),
              Column('username', String(50), nullable=False, unique=True),
              Column('password', String(255), nullable=False),  # Plain password
              Column('email', String(100), nullable=False, unique=True),
              Column('is_robot', Boolean, default=False))  # Robot check column

metadata.create_all(engine)

# טבלת הפגישות
appointments = Table('appointments', metadata,
                     Column('appointment_id', Integer, primary_key=True),
                     Column('client_name', String(100), nullable=False),
                     Column('doctor_name', String(50), nullable=False),
                     Column('email', String(100), nullable=False),
                     Column('phone', String(20)),
                     Column('date', Date, nullable=False),
                     Column('message', Text))

# יצירת הטבלאות במסד הנתונים (במידה והן לא קיימות)
metadata.create_all(engine)


# פונקציה להוספת פגישה
def add_appointment(client_name, doctor_name, email, phone, date, message):
    # יצירת סשן חדש
    session = Session()
    try:
        # הוספת הרשומה לסשן
        insert_stmt = appointments.insert().values(
            client_name=client_name,
            doctor_name=doctor_name,
            email=email,
            phone=phone,
            date=date,
            message=message
        )
        session.execute(insert_stmt)
        # שמירת השינויים במסד הנתונים
        session.commit()
        print("Appointment added successfully!")  # הודעה להדפסה
    except Exception as e:
        session.rollback()  # אם יש שגיאה, החזר את השינויים
        print(f"Error adding appointment: {e}")  # טיפול בשגיאות
    finally:
        session.close()  # סגירת הסשן

# פונקציה לשליפת רשימת הפגישות
def get_appointments():
    try:
        select_stmt = select([appointments]) # שאילתה לבחירת כל הפגישות
        with engine.connect() as conn:
            result = conn.execute(select_stmt)  # ביצוע השאילתה
            appointments_list = result.fetchall() # הבאת התוצאות
        return appointments_list
    except Exception as e:
        print(f"Error retrieving appointments: {e}")
        return []


# פונקציות CRUD (הוספה, מחיקה, עדכון)
def add_doctor(name, seniority, age, category, image_url, description):
    insert_stmt = doctors.insert().values(
        dr_name=name,
        dr_seniority=seniority,
        dr_age=age,
        dr_category=category,
        dr_image_url=image_url,  # הוספת כתובת התמונה
        dr_description=description  # הוספת תיאור הרופא
    )
    session.execute(insert_stmt)  # ביצוע פעולת ההוספה
    session.commit() # שמירת השינויים


def delete_doctor(doctor_id):
    delete_stmt = doctors.delete().where(doctors.c.dr_id == doctor_id)
    session.execute(delete_stmt)
    session.commit()


def update_doctor(doctor_id, name, seniority, age, category, image_url, description):
    update_stmt = doctors.update().where(doctors.c.dr_id == doctor_id).values(
        dr_name=name,
        dr_seniority=seniority,
        dr_age=age,
        dr_category=category,
        dr_image_url=image_url,  # עדכון כתובת התמונה
        dr_description=description  # עדכון תיאור הרופא
    )
    session.execute(update_stmt)
    session.commit()

# פונקציה להוספת משתמש חדש
def add_user(username, password, email, ):
    hashed_password = generate_password_hash(password) # יצירת סיסמה מוצפנת
    insert_stmt = users.insert().values(
        username=username,
        password=hashed_password,  # שמירת הסיסמה המוצפנת
        email=email,

    )
    session.execute(insert_stmt)
    session.commit()

def delete_user(user_id):
    delete_stmt = users.delete().where(users.c.id == user_id)
    session.execute(delete_stmt)
    session.commit()

def update_user(user_id, username=None, password=None, email=None, ):
    update_values = {}
    if username:
        update_values['username'] = username
    if password:
        update_values['password'] = password  # Store password as plain text
    if email:
        update_values['email'] = email


    update_stmt = users.update().where(users.c.id == user_id).values(**update_values)
    session.execute(update_stmt)
    session.commit()


def get_user_by_username(username):
    select_stmt = users.select().where(users.c.username == username)
    return session.execute(select_stmt).fetchone()

def get_user_by_email(user_email):
    select_stmt = users.select().where(users.c.username == user_email)
    return session.execute(select_stmt).fetchone()

def get_user_by_id(user_id):
    select_stmt = users.select().where(users.c.id == user_id)
    return session.execute(select_stmt).fetchone()


def get_user_by_password(password):
    select_stmt = users.select().where(users.c.password == password)
    return session.execute(select_stmt).fetchone()
