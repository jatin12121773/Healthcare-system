from flask import Flask, render_template, request
import sqlite3
import pandas as pd

app = Flask(__name__)

# ---------------- DATABASE ---------------- #

def connect_db():
    conn = sqlite3.connect("patients.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            blood_group TEXT,
            phone TEXT,
            symptoms TEXT,
            disease TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOAD DATASET ---------------- #

symptoms_df = pd.read_csv("dataset.csv")
precautions_df = pd.read_csv("disease_dataset.csv")

# Clean column names
symptoms_df.columns = [col.strip().lower() for col in symptoms_df.columns]
precautions_df.columns = [col.strip().lower() for col in precautions_df.columns]

# Extract unique symptoms
all_symptoms = set()
for col in symptoms_df.columns[1:]:
    all_symptoms.update(symptoms_df[col].dropna().unique())

all_symptoms = sorted(all_symptoms)

blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ---------------- ROUTE ---------------- #

@app.route("/", methods=["GET", "POST"])
def form():

    if request.method == "POST":

        name = request.form.get("name")
        age = request.form.get("age")
        blood = request.form.get("blood")
        phone = request.form.get("phone")
        selected_symptoms = request.form.getlist("symptoms")

        # ---------------- Disease Prediction ---------------- #

        best_match = None
        max_match = 0

        for index, row in symptoms_df.iterrows():
            disease_symptoms = row[1:].dropna().tolist()
            match_count = len(set(selected_symptoms) & set(disease_symptoms))

            if match_count > max_match:
                max_match = match_count
                best_match = row["disease"]

        # ---------------- Get Precautions ---------------- #

        precautions = []
        if best_match:
            prec_row = precautions_df[precautions_df["disease"] == best_match]
            if not prec_row.empty:
                precautions = [
                    str(prec_row.iloc[0][col])
                    for col in prec_row.columns[1:]
                    if pd.notna(prec_row.iloc[0][col])
                ]

        # ---------------- Save To Database ---------------- #

        symptoms_string = ", ".join(selected_symptoms)

        conn = connect_db()
        conn.execute("""
            INSERT INTO patients(name, age, blood_group, phone, symptoms, disease)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, age, blood, phone, symptoms_string, best_match))
        conn.commit()
        conn.close()

        # ---------------- Render Result ---------------- #

        return render_template(
            "result.html",
            name=name,
            age=age,
            selected_symptoms=selected_symptoms,
            disease=best_match,
            precautions=precautions
        )

    return render_template(
        "disease_form.html",
        symptoms=all_symptoms,
        blood_groups=blood_groups
    )

if __name__ == "__main__":
    app.run(debug=True)