"""
Database layer for the Hospital Management System (SQLite).

The HospitalDB class holds every operation the app needs:
login, patients, doctors, appointments, medical records and billing.
All inputs pass through validators.py before being saved.
"""
import sqlite3
from contextlib import closing

import validators as v

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    phone TEXT NOT NULL,
    disease TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    phone TEXT NOT NULL,
    fee REAL NOT NULL,
    available INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Scheduled'
);
CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    visit_date TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment TEXT NOT NULL,
    prescription TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    consultation_charge REAL NOT NULL,
    treatment_charge REAL NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unpaid'
);
"""


class HospitalDB:
    def __init__(self, path):
        self.path = path
        with closing(self._connect()) as conn:
            conn.executescript(SCHEMA)
            # Default login for the demo: admin / admin123
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                ("admin", "admin123"),
            )
            conn.commit()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row  # rows behave like dictionaries
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # closing(...) makes sure every connection is closed after use
    def _query(self, sql, params=()):
        with closing(self._connect()) as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def _execute(self, sql, params=()):
        with closing(self._connect()) as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.lastrowid

    # ---------------- Login ----------------
    def check_login(self, username, password):
        rows = self._query(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        return len(rows) == 1

    # ---------------- Patients ----------------
    def _clean_patient(self, name, age, gender, phone, disease):
        return (
            v.validate_name(name),
            v.validate_age(age),
            v.validate_gender(gender),
            v.validate_phone(phone),
            v.validate_text(disease, "Disease"),
        )

    def add_patient(self, name, age, gender, phone, disease):
        return self._execute(
            "INSERT INTO patients (name, age, gender, phone, disease) VALUES (?, ?, ?, ?, ?)",
            self._clean_patient(name, age, gender, phone, disease),
        )

    def update_patient(self, patient_id, name, age, gender, phone, disease):
        if not self.get_patient(patient_id):
            raise ValueError("Patient not found.")
        self._execute(
            "UPDATE patients SET name = ?, age = ?, gender = ?, phone = ?, disease = ? "
            "WHERE id = ?",
            self._clean_patient(name, age, gender, phone, disease) + (patient_id,),
        )

    def get_patients(self, search=""):
        """Search by patient ID (if a number is typed) or by part of the name."""
        search = (search or "").strip()
        if search.isdigit():
            return self._query("SELECT * FROM patients WHERE id = ?", (int(search),))
        return self._query(
            "SELECT * FROM patients WHERE name LIKE ? ORDER BY id", (f"%{search}%",)
        )

    def get_patient(self, patient_id):
        rows = self._query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        return rows[0] if rows else None

    def delete_patient(self, patient_id):
        if not self.get_patient(patient_id):
            raise ValueError("Patient not found.")
        self._execute("DELETE FROM patients WHERE id = ?", (patient_id,))

    # ---------------- Doctors ----------------
    def _clean_doctor(self, name, specialization, phone, fee):
        return (
            v.validate_name(name),
            v.validate_text(specialization, "Specialization"),
            v.validate_phone(phone),
            v.validate_amount(fee, "Fee"),
        )

    def add_doctor(self, name, specialization, phone, fee):
        return self._execute(
            "INSERT INTO doctors (name, specialization, phone, fee) VALUES (?, ?, ?, ?)",
            self._clean_doctor(name, specialization, phone, fee),
        )

    def update_doctor(self, doctor_id, name, specialization, phone, fee):
        if not self.get_doctor(doctor_id):
            raise ValueError("Doctor not found.")
        self._execute(
            "UPDATE doctors SET name = ?, specialization = ?, phone = ?, fee = ? WHERE id = ?",
            self._clean_doctor(name, specialization, phone, fee) + (doctor_id,),
        )

    def get_doctors(self, search=""):
        """Search by doctor name or specialization."""
        like = f"%{(search or '').strip()}%"
        return self._query(
            "SELECT * FROM doctors WHERE name LIKE ? OR specialization LIKE ? ORDER BY id",
            (like, like),
        )

    def get_doctor(self, doctor_id):
        rows = self._query("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        return rows[0] if rows else None

    def toggle_availability(self, doctor_id):
        if not self.get_doctor(doctor_id):
            raise ValueError("Doctor not found.")
        self._execute(
            "UPDATE doctors SET available = 1 - available WHERE id = ?", (doctor_id,)
        )

    def delete_doctor(self, doctor_id):
        if not self.get_doctor(doctor_id):
            raise ValueError("Doctor not found.")
        self._execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))

    # ---------------- Appointments ----------------
    def book_appointment(self, patient_id, doctor_id, date, time):
        if not self.get_patient(patient_id):
            raise ValueError("Please select a valid patient.")
        doctor = self.get_doctor(doctor_id)
        if not doctor:
            raise ValueError("Please select a valid doctor.")
        if not doctor["available"]:
            raise ValueError("This doctor is not available right now.")
        date = v.validate_appointment_date(date)
        time = v.validate_time_slot(time)
        # Business rule: a doctor cannot have two appointments at the same time
        clash = self._query(
            "SELECT id FROM appointments WHERE doctor_id = ? AND date = ? AND time = ? "
            "AND status = 'Scheduled'",
            (doctor_id, date, time),
        )
        if clash:
            raise ValueError("This doctor is already booked for that date and time.")
        # Business rule: a patient cannot be in two appointments at the same time
        clash = self._query(
            "SELECT id FROM appointments WHERE patient_id = ? AND date = ? AND time = ? "
            "AND status = 'Scheduled'",
            (patient_id, date, time),
        )
        if clash:
            raise ValueError("This patient already has an appointment at that date and time.")
        return self._execute(
            "INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES (?, ?, ?, ?)",
            (patient_id, doctor_id, date, time),
        )

    def get_appointments(self):
        return self._query(
            "SELECT a.*, p.name AS patient_name, d.name AS doctor_name "
            "FROM appointments a "
            "JOIN patients p ON p.id = a.patient_id "
            "JOIN doctors d ON d.id = a.doctor_id "
            "ORDER BY a.date, a.time"
        )

    def get_appointment(self, appointment_id):
        rows = self._query("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        return rows[0] if rows else None

    def cancel_appointment(self, appointment_id):
        if not self.get_appointment(appointment_id):
            raise ValueError("Appointment not found.")
        self._execute(
            "UPDATE appointments SET status = 'Cancelled' WHERE id = ?", (appointment_id,)
        )

    # ---------------- Medical Records ----------------
    def add_medical_record(self, patient_id, visit_date, diagnosis, treatment, prescription):
        if not self.get_patient(patient_id):
            raise ValueError("Please select a valid patient.")
        return self._execute(
            "INSERT INTO medical_records (patient_id, visit_date, diagnosis, treatment, "
            "prescription) VALUES (?, ?, ?, ?, ?)",
            (
                patient_id,
                v.validate_visit_date(visit_date),
                v.validate_text(diagnosis, "Diagnosis"),
                v.validate_text(treatment, "Treatment"),
                v.validate_text(prescription, "Prescription"),
            ),
        )

    def get_medical_records(self, patient_id=None):
        """All records, or the full history of one patient (newest first)."""
        sql = (
            "SELECT r.*, p.name AS patient_name FROM medical_records r "
            "JOIN patients p ON p.id = r.patient_id "
        )
        if patient_id:
            return self._query(sql + "WHERE r.patient_id = ? ORDER BY r.visit_date DESC",
                               (patient_id,))
        return self._query(sql + "ORDER BY r.visit_date DESC")

    # ---------------- Billing ----------------
    def create_bill(self, patient_id, consultation_charge, treatment_charge):
        if not self.get_patient(patient_id):
            raise ValueError("Please select a valid patient.")
        consultation = v.validate_charge(consultation_charge, "Consultation charge")
        treatment = v.validate_charge(treatment_charge, "Treatment charge")
        total = round(consultation + treatment, 2)  # total amount is calculated here
        if total <= 0:
            raise ValueError("Total amount must be greater than 0.")
        return self._execute(
            "INSERT INTO bills (patient_id, consultation_charge, treatment_charge, total) "
            "VALUES (?, ?, ?, ?)",
            (patient_id, consultation, treatment, total),
        )

    def get_bills(self):
        return self._query(
            "SELECT b.*, p.name AS patient_name FROM bills b "
            "JOIN patients p ON p.id = b.patient_id ORDER BY b.id"
        )

    def mark_bill_paid(self, bill_id):
        if not self._query("SELECT id FROM bills WHERE id = ?", (bill_id,)):
            raise ValueError("Bill not found.")
        self._execute("UPDATE bills SET status = 'Paid' WHERE id = ?", (bill_id,))

    # ---------------- Dashboard ----------------
    def get_stats(self):
        def count(sql):
            return self._query(sql)[0]["n"]

        return {
            "patients": count("SELECT COUNT(*) AS n FROM patients"),
            "doctors": count("SELECT COUNT(*) AS n FROM doctors"),
            "appointments": count(
                "SELECT COUNT(*) AS n FROM appointments WHERE status = 'Scheduled'"
            ),
            "records": count("SELECT COUNT(*) AS n FROM medical_records"),
            "unpaid_bills": count("SELECT COUNT(*) AS n FROM bills WHERE status = 'Unpaid'"),
        }

    def seed_sample_data(self):
        """Adds a few sample doctors so the demo is not empty."""
        if self.get_doctors():
            return
        self.add_doctor("Dr. Ramesh Kumar", "Cardiologist", "9876543210", 500)
        self.add_doctor("Dr. Priya Sharma", "Pediatrician", "9876501234", 400)
        self.add_doctor("Dr. Anil Reddy", "Orthopedic", "9123456780", 450)

    def reset(self):
        """Deletes all patients, doctors, appointments, records and bills and starts the
        IDs again at 1. The admin login stays and the sample doctors are added again.
        Used so that every live demo (run.py) starts with a clean app."""
        with closing(self._connect()) as conn:
            conn.executescript(
                "DELETE FROM bills; DELETE FROM medical_records; DELETE FROM appointments;"
                "DELETE FROM patients; DELETE FROM doctors;"
                "DELETE FROM sqlite_sequence WHERE name <> 'users';"
            )
            conn.commit()
        self.seed_sample_data()
