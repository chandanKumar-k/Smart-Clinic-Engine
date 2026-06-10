import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import sqlite3
import datetime

# Import data fetch engine from database layer
from database import fetch_training_data, DB_NAME

st.set_page_config(page_title="Smart Clinic Scheduler", page_icon="🏥", layout="centered")

st.title("🏥 Smart Clinic Engine & Appointment Optimizer")
st.write("Dynamic scheduling optimization powered by Machine Learning and Relational SQL Databases.")

# 1. TRAIN MACHINE LEARNING MODEL ON HISTORICAL APPOINTMENT DATA
@st.cache_resource
def train_scheduler_model():
    df = fetch_training_data()
    X = df[['Age', 'Gender', 'DoctorName', 'Symptoms', 'Severity']]
    y = df['ActualDuration']
    
    categorical_features = ['Gender', 'DoctorName', 'Symptoms', 'Severity']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[('cat', categorical_transformer, categorical_features)],
        remainder='passthrough'
    )
    
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))
    ])
    
    model_pipeline.fit(X, y)
    return model_pipeline

try:
    model = train_scheduler_model()
except Exception as e:
    st.error("Make sure you have run 'python database.py' first to initialize your records!")
    st.stop()

st.markdown("---")
st.subheader("📋 Patient Booking Registration")

col1, col2 = st.columns(2)

with col1:
    patient_name = st.text_input("Patient Full Name", placeholder="Rahul Sharma")
    age = st.number_input("Age", min_value=1, max_value=110, value=25)
    gender = st.selectbox("Gender", ["Male", "Female"])

with col2:
    doctor = st.selectbox("Select Specialist", ["Dr. Abhinav Rao", "Dr. Meera Nair", "Dr. Sathish Kumar"])
    symptoms = st.selectbox("Primary Symptoms", ["Fever & Cold", "Migraine Headache", "Chest Discomfort", "Routine Body Checkup", "Stomach Pain"])
    severity = st.selectbox("Severity Classification", ["Low", "Medium", "High"])

# 2. SEAMLESS TIMELINE ALLOCATION ENGINE (TODAY ONLY LOGIC)
def calculate_next_available_time(doctor_name, today_date):
    """Queries the database to find active bookings specifically for TODAY."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Strictly isolates entries recorded under today's date stamp
    cursor.execute("""
        SELECT a.Time, a.ActualDuration 
        FROM Appointments a
        JOIN Doctors d ON a.DoctorID = d.DoctorID
        WHERE d.Name = ? AND a.Date = ?
        ORDER BY a.AppointmentID DESC LIMIT 1
    """, (doctor_name, today_date))
    
    last_appointment = cursor.fetchone()
    conn.close()
    
    # If no appointments are booked yet TODAY, start fresh at 09:00 AM
    if not last_appointment:
        return "09:00 AM"
        
    last_time_str, last_duration = last_appointment
    
    # Parse the string time into time object structure robustly
    try:
        start_time = datetime.datetime.strptime(last_time_str, "%I:%M %p")
    except ValueError:
        start_time = datetime.datetime.strptime(last_time_str, "%H:%M")
        
    # Stack the duration on top of the last slot's start time
    next_time = start_time + datetime.timedelta(minutes=int(last_duration))
    
    return next_time.strftime("%I:%M %p")

# 3. INTERACTIVE SCHEDULING DISPATCH LOOP
if st.button("Calculate Optimized Booking Slot", type="primary"):
    if patient_name.strip() == "":
        st.warning("Please provide a valid Patient Name to schedule the database row entry.")
    else:
        input_data = pd.DataFrame([{
            'Age': age,
            'Gender': gender,
            'DoctorName': doctor,
            'Symptoms': symptoms,
            'Severity': severity
        }])
        
        # ML Prediction Calculation
        predicted_minutes = int(round(model.predict(input_data)[0]))
        
        # Get active runtime tracking parameters
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        allocated_arrival_time = calculate_next_available_time(doctor, today_str)
        
        st.success(f"🎉 Appointment Optimized Successfully for {patient_name}!")
        
        # UI Metrics Layout
        m1, m2 = st.columns(2)
        m1.metric(label="Your Scheduled Arrival Time", value=f"{allocated_arrival_time}")
        m2.metric(label="Calculated Slot Duration", value=f"{predicted_minutes} Mins")
        
        # Compute appointment exit time boundary cleanly
        try:
            parsed_arrival = datetime.datetime.strptime(allocated_arrival_time, '%I:%M %p')
        except ValueError:
            parsed_arrival = datetime.datetime.strptime(allocated_arrival_time, '%H:%M')
            
        conclude_time = (parsed_arrival + datetime.timedelta(minutes=predicted_minutes)).strftime('%I:%M %p')
        st.info(f"ℹ️ **Doctor Availability Note:** {doctor} is completely free at **{allocated_arrival_time}**. Your session will safely conclude at **{conclude_time}**.")
            
        # Commit fresh entry into operational relational database rows
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO Patients (Name, Age, Gender) VALUES (?, ?, ?)", (patient_name, age, gender))
            p_id = cursor.lastrowid
            
            cursor.execute("SELECT DoctorID FROM Doctors WHERE Name = ?", (doctor,))
            d_id = cursor.fetchone()[0] # Target inner primitive key cleanly
            
            cursor.execute("""
                INSERT INTO Appointments (PatientID, DoctorID, Date, Time, Symptoms, Severity, ActualDuration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (p_id, d_id, today_str, allocated_arrival_time, symptoms, severity, predicted_minutes))
            
            conn.commit()
            conn.close()
            st.caption("💾 Relational timeline updated. Records safely stored inside `clinic.db`.")
        except Exception as database_err:
            st.error(f"Database sync lag encountered: {database_err}")

# 4. LIVE SCHEDULE VISUALIZATION BLOCK (DBMS LIVE CHECK)
st.markdown("---")
st.subheader("📊 Today's Active Live Booking Queue")
try:
    conn = sqlite3.connect(DB_NAME)
    today_date_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # Query database live rows matching today's parameters to display a tracking chart
    view_query = """
        SELECT p.Name as Patient, d.Name as Doctor, a.Time as [Arrival Time], a.ActualDuration || ' Mins' as [Duration Slot], a.Symptoms
        FROM Appointments a
        JOIN Patients p ON a.PatientID = p.PatientID
        JOIN Doctors d ON a.DoctorID = d.DoctorID
        WHERE a.Date = ?
        ORDER BY a.AppointmentID ASC
    """
    live_df = pd.read_sql_query(view_query, conn, params=(today_date_str,))
    conn.close()
    
    if not live_df.empty:
        st.dataframe(live_df, use_container_width=True, hide_index=True)
    else:
        st.info("🌱 The active timeline matrix for today is currently open and clear. First booking will register at 09:00 AM.")
except Exception as table_err:
    st.caption(f"Waiting for first active row validation parameters: {table_err}")

# if u want to run agian from 9 : 00 AM --> u should just delete clinic.db and run again python database.py and again open new terminal then again start app.py