from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "healthcare_secret"


# ---------------- DATABASE CONNECTION ---------------- #

def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INITIALIZE DATABASE ---------------- #

def init_db():

    conn = connect_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        blood_group TEXT,
        phone TEXT,
        symptoms TEXT,
        disease TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        date TEXT,
        comment TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS contacts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- LOAD DATASETS ---------------- #

symptoms_df = pd.read_csv("dataset.csv")
precautions_df = pd.read_csv("disease_dataset.csv")

symptoms_df.columns = symptoms_df.columns.str.strip().str.lower()
precautions_df.columns = precautions_df.columns.str.strip().str.lower()

symptoms_df["disease"] = symptoms_df["disease"].astype(str).str.lower().str.strip()
precautions_df["disease"] = precautions_df["disease"].astype(str).str.lower().str.strip()

for col in symptoms_df.columns[1:]:
    symptoms_df[col] = symptoms_df[col].astype(str).str.lower()


# ---------------- EXTRACT ALL SYMPTOMS ---------------- #

all_symptoms = []

for col in symptoms_df.columns[1:]:
    for symptom in symptoms_df[col].dropna():
        if symptom not in all_symptoms:
            all_symptoms.append(symptom)

all_symptoms.sort()

blood_groups = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SIGNUP ---------------- #

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = connect_db()

        try:
            conn.execute(
                "INSERT INTO users(fullname,email,password) VALUES(?,?,?)",
                (fullname,email,password)
            )
            conn.commit()
            conn.close()

            return redirect(url_for("signin"))

        except:
            conn.close()
            return "Email already exists"

    return render_template("signup.html")


# ---------------- SIGNIN ---------------- #

@app.route("/signin", methods=["GET","POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"],password):

            session["user"] = user["fullname"]

            # 🔥 Redirect to disease page
            return redirect(url_for("disease"))

        else:
            return "Invalid Email or Password"

    return render_template("signin.html")


# ---------------- DISEASE PREDICTION ---------------- #
@app.route("/admin-login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if email == "jatinmehra7665@gmail.com" and password == "jatin2@&#":
            session["admin"] = True   # ✅ session set
            return redirect("/admin") # ✅ dashboard open
        else:
            return "<script>alert('Wrong Password');</script>"

    return render_template("admin_login.html")
# ---------------- ADMIN PANEL ---------------- #
@app.route("/admin")
def admin():

    # 🚫 Agar login nahi hai → login page pe bhejo
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    # ✅ Login ho gaya → dashboard open
    conn = connect_db()

    users = conn.execute("SELECT * FROM users").fetchall()
    patients = conn.execute("SELECT * FROM patients").fetchall()
    appointments = conn.execute("SELECT * FROM appointments").fetchall()
    contacts = conn.execute("SELECT * FROM contacts").fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        patients=patients,
        appointments=appointments,
        contacts=contacts
    )


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin-login")



    

@app.route("/disease", methods=["GET","POST"])
def disease():

    if "user" not in session:
        return redirect(url_for("signin"))

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        blood = request.form["blood"]
        phone = request.form["phone"]

        selected_symptoms = request.form.getlist("symptoms")

        best_match = None
        max_match = 0

        for index,row in symptoms_df.iterrows():

            disease_symptoms = row[1:].dropna().tolist()

            match_count = len(set(selected_symptoms) & set(disease_symptoms))

            if match_count > max_match:
                max_match = match_count
                best_match = row["disease"]

        symptoms_string = ", ".join(selected_symptoms)

        conn = connect_db()

        conn.execute("""
        INSERT INTO patients(name,age,blood_group,phone,symptoms,disease)
        VALUES(?,?,?,?,?,?)
        """,(name,age,blood,phone,symptoms_string,best_match))

        conn.commit()
        conn.close()

        # -------- PRECAUTIONS -------- #

        precautions = []

        if best_match:

            best_match = best_match.lower().strip()

            p = precautions_df[precautions_df["disease"] == best_match]

            if not p.empty:
                precautions = p.iloc[0,1:].dropna().tolist()

        return render_template(
            "result.html",
            name=name,
            age=age,
            symptoms=selected_symptoms,
            disease=best_match,
            precautions=precautions
        )

    return render_template(
        "disease_form.html",
        symptoms=all_symptoms,
        blood_groups=blood_groups
    )


# ---------------- APPOINTMENT ---------------- #

@app.route("/appointment", methods=["POST"])
def appointment():

    print(request.form)  # 👈 DEBUG

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    date = request.form["date"]
    comment = request.form["comment"] 

    conn = connect_db()

    conn.execute(
        "INSERT INTO appointments(name,email,phone,date,comment) VALUES(?,?,?,?,?)",
        (name,email,phone,date,comment)
    )

    conn.commit()
    conn.close()

    return render_template("index.html", appointment_success=True)
# ---------------- CONTACT ---------------- #

@app.route("/contact", methods=["POST"])
def contact():

    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    conn = connect_db()

    conn.execute(
        "INSERT INTO contacts(name,email,message) VALUES(?,?,?)",
        (name,email,message)
    )

    conn.commit()
    conn.close()

    return render_template("index.html", contact_success=True)


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():



    session.pop("user",None)

    return redirect(url_for("home"))


# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    app.run(debug=True)