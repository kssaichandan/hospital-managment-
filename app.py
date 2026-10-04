"""
Hospital Management System - Flask web application.

Run:   python app.py
Open:  http://127.0.0.1:5000   (login: admin / admin123)
"""
from datetime import date
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database import HospitalDB
from validators import GENDERS, TIME_SLOTS


def create_app(db_path="hospital.db", seed=False):
    app = Flask(__name__)
    app.secret_key = "hms-demo-secret-key"
    db = HospitalDB(db_path)
    if seed:
        db.seed_sample_data()
    app.config["DB"] = db

    def login_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not session.get("user"):
                flash("Please log in first.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapper

    def run_action(action, success_message):
        """Runs a database action and shows a green success or red error message.
        Returns True if the action worked."""
        try:
            action()
            flash(success_message, "success")
            return True
        except ValueError as error:
            flash(str(error), "error")
            return False

    # ---------------- Login / Logout ----------------
    @app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            if db.check_login(request.form.get("username"), request.form.get("password")):
                session["user"] = request.form["username"]
                flash("Login successful.", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    # ---------------- Dashboard ----------------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", stats=db.get_stats())

    # ---------------- Patients ----------------
    @app.route("/patients", methods=["GET", "POST"])
    @login_required
    def patients():
        if request.method == "POST":
            f = request.form
            run_action(
                lambda: db.add_patient(f.get("name"), f.get("age"), f.get("gender"),
                                       f.get("phone"), f.get("disease")),
                "Patient added successfully.",
            )
            return redirect(url_for("patients"))
        search = request.args.get("search", "")
        return render_template("patients.html", patients=db.get_patients(search),
                               search=search, genders=GENDERS)

    @app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_patient(patient_id):
        patient = db.get_patient(patient_id)
        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients"))
        if request.method == "POST":
            f = request.form
            if run_action(
                lambda: db.update_patient(patient_id, f.get("name"), f.get("age"),
                                          f.get("gender"), f.get("phone"), f.get("disease")),
                "Patient details updated successfully.",
            ):
                return redirect(url_for("patients"))
            patient = dict(patient, **f.to_dict())  # keep what the user typed
        return render_template("edit_patient.html", patient=patient, genders=GENDERS)

    @app.route("/patients/<int:patient_id>/delete", methods=["POST"])
    @login_required
    def delete_patient(patient_id):
        run_action(lambda: db.delete_patient(patient_id), "Patient removed successfully.")
        return redirect(url_for("patients"))

    # ---------------- Doctors ----------------
    @app.route("/doctors", methods=["GET", "POST"])
    @login_required
    def doctors():
        if request.method == "POST":
            f = request.form
            run_action(
                lambda: db.add_doctor(f.get("name"), f.get("specialization"),
                                      f.get("phone"), f.get("fee")),
                "Doctor added successfully.",
            )
            return redirect(url_for("doctors"))
        search = request.args.get("search", "")
        return render_template("doctors.html", doctors=db.get_doctors(search), search=search)

    @app.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_doctor(doctor_id):
        doctor = db.get_doctor(doctor_id)
        if not doctor:
            flash("Doctor not found.", "error")
            return redirect(url_for("doctors"))
        if request.method == "POST":
            f = request.form
            if run_action(
                lambda: db.update_doctor(doctor_id, f.get("name"), f.get("specialization"),
                                         f.get("phone"), f.get("fee")),
                "Doctor details updated successfully.",
            ):
                return redirect(url_for("doctors"))
            doctor = dict(doctor, **f.to_dict())
        return render_template("edit_doctor.html", doctor=doctor)

    @app.route("/doctors/<int:doctor_id>/availability", methods=["POST"])
    @login_required
    def toggle_availability(doctor_id):
        run_action(lambda: db.toggle_availability(doctor_id), "Doctor availability updated.")
        return redirect(url_for("doctors"))

    @app.route("/doctors/<int:doctor_id>/delete", methods=["POST"])
    @login_required
    def delete_doctor(doctor_id):
        run_action(lambda: db.delete_doctor(doctor_id), "Doctor removed successfully.")
        return redirect(url_for("doctors"))

    # ---------------- Appointments ----------------
    @app.route("/appointments", methods=["GET", "POST"])
    @login_required
    def appointments():
        if request.method == "POST":
            f = request.form
            run_action(
                lambda: db.book_appointment(f.get("patient_id"), f.get("doctor_id"),
                                            f.get("date"), f.get("time")),
                "Appointment booked successfully.",
            )
            return redirect(url_for("appointments"))
        return render_template("appointments.html", appointments=db.get_appointments(),
                               patients=db.get_patients(), doctors=db.get_doctors(),
                               time_slots=TIME_SLOTS, today=date.today().isoformat())

    @app.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
    @login_required
    def cancel_appointment(appointment_id):
        run_action(lambda: db.cancel_appointment(appointment_id), "Appointment cancelled.")
        return redirect(url_for("appointments"))

    # ---------------- Medical Records ----------------
    @app.route("/records", methods=["GET", "POST"])
    @login_required
    def records():
        if request.method == "POST":
            f = request.form
            run_action(
                lambda: db.add_medical_record(f.get("patient_id"), f.get("visit_date"),
                                              f.get("diagnosis"), f.get("treatment"),
                                              f.get("prescription")),
                "Medical record saved successfully.",
            )
            return redirect(url_for("records"))
        patient_id = request.args.get("patient_id", type=int)
        return render_template("records.html", records=db.get_medical_records(patient_id),
                               patients=db.get_patients(), selected=patient_id,
                               today=date.today().isoformat())

    # ---------------- Billing ----------------
    @app.route("/billing", methods=["GET", "POST"])
    @login_required
    def billing():
        if request.method == "POST":
            f = request.form
            run_action(
                lambda: db.create_bill(f.get("patient_id"), f.get("consultation_charge"),
                                       f.get("treatment_charge")),
                "Bill generated successfully.",
            )
            return redirect(url_for("billing"))
        return render_template("billing.html", bills=db.get_bills(), patients=db.get_patients())

    @app.route("/billing/<int:bill_id>/pay", methods=["POST"])
    @login_required
    def pay_bill(bill_id):
        run_action(lambda: db.mark_bill_paid(bill_id), "Bill marked as paid.")
        return redirect(url_for("billing"))

    return app


if __name__ == "__main__":
    create_app(seed=True).run(debug=True)
