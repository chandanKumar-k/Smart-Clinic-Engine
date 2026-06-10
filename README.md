# Smart Clinic Engine & Appointment Optimizer 🏥

An industry-track intelligent healthcare scheduling dashboard built with **Python**, **Streamlit**, and **SQLite** to optimize operational patient throughput using Machine Learning pipelines.

## 🚀 Architectural Pillars
* **DBMS Layer (3NF Relational Structure)**: Implements fully normalized SQL schemas using strict **Foreign Key constraints** to enforce absolute data referential integrity across `Patients`, `Doctors`, and `Appointments` tracking tables.
* **ML Layer (Predictive Optimization)**: Utilizes a `RandomForestRegressor` pipeline combined with a `OneHotEncoder` data transformer to dynamically predict transaction processing time blocks based on patient criteria (Age, Symptoms, Severity, Specialist allocation).
* **Dynamic Timeline Tracking**: Bypasses rigid calendar systems by running localized SQL subqueries to automatically calculate and assign clean AM/PM arrival slots based on ongoing doctor availability.

## 🛠️ Tech Stack & Dependencies
* **Core Language**: Python 3
* **Database Engine**: SQLite 3 (Raw SQL Queries, Subqueries, & Joins)
* **Data Processing & ML**: Scikit-Learn, Pandas, NumPy
* **Interface Architecture**: Streamlit Web Server Framework

## ⚙️ Quick Local Initialization
1. Initialize the relational database schemas and inject historical baseline rows:
   ```bash
   python database.py
   ```
2. Spin up the localized Machine Learning scheduling engine dashboard:
   ```bash
   python -m streamlit run app.py
   ```

