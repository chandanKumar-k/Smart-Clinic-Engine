import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

DB_NAME = "clinic.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DROP TABLE IF EXISTS Appointments;")
    cursor.execute("DROP TABLE IF EXISTS Patients;")
    cursor.execute("DROP TABLE IF EXISTS Doctors;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE Patients (
        PatientID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Age INTEGER NOT NULL,
        Gender TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE Doctors (
        DoctorID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Specialization TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Appointments (
        AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        PatientID INTEGER NOT NULL,
        DoctorID INTEGER NOT NULL,
        Date TEXT NOT NULL,
        Time TEXT NOT NULL,
        Symptoms TEXT NOT NULL,
        Severity TEXT NOT NULL,
        ActualDuration INTEGER NOT NULL,
        FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE,
        FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def inject_mock_data():
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()

    doctors = [
        ("Dr. Abhinav Rao", "General Medicine"),
        ("Dr. Meera Nair", "Pediatrics"),
        ("Dr. Sathish Kumar", "Cardiology")
    ]
    cursor.executemany("INSERT INTO Doctors (Name, Specialization) VALUES (?, ?)", doctors)
    conn.commit()

    cursor.execute("SELECT DoctorID FROM Doctors")
    valid_doctor_ids = [row[0] for row in cursor.fetchall()]

    first_names = ["Rahul", "Priya", "Amit", "Ananya", "Vikram", "Sneha", "Karan", "Kavitha", "Vijay", "Deepa"]
    last_names = ["Sharma", "Verma", "Hegde", "Patil", "Rao", "Joshi", "Kumar", "Gowda", "Shetty", "Nair"]
    genders = ["Male", "Female"]
    symptom_pool = ["Fever & Cold", "Migraine Headache", "Chest Discomfort", "Routine Body Checkup", "Stomach Pain"]
    severities = ["Low", "Medium", "High"]

    base_date = datetime.now()
    
    for i in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(5, 75)
        gender = random.choice(genders)
        cursor.execute("INSERT INTO Patients (Name, Age, Gender) VALUES (?, ?, ?)", (name, age, gender))
        patient_id = cursor.lastrowid

        doctor_id = random.choice(valid_doctor_ids)
        symptoms = random.choice(symptom_pool)
        severity = random.choice(severities)
        
        base_time = 10
        if severity == "Medium": base_time += 5
        elif severity == "High": base_time += 12
        if "Chest" in symptoms or "Migraine" in symptoms: base_time += 8
        if age > 60 or age < 10: base_time += 4
        
        actual_duration = base_time + random.randint(-2, 3)
        
        # CRITICAL FIX: Make sure random data generation starts from at least 1 day ago (Yesterday)
        app_date = (base_date - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        app_time = f"{random.randint(9, 16)}:00"

        cursor.execute("""
            INSERT INTO Appointments (PatientID, DoctorID, Date, Time, Symptoms, Severity, ActualDuration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, app_date, app_time, symptoms, severity, actual_duration))

    conn.commit()
    conn.close()
    print("🎯 Clean Historical Database Initialized (Today's queue is completely clear!).")

def fetch_training_data():
    conn = get_connection()
    query = """
        SELECT p.Age, p.Gender, d.Name as DoctorName, a.Symptoms, a.Severity, a.ActualDuration
        FROM Appointments a
        JOIN Patients p ON a.PatientID = p.PatientID
        JOIN Doctors d ON a.DoctorID = d.DoctorID
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
    
if __name__ == "__main__":
    inject_mock_data()
