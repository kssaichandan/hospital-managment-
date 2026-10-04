"""INTEGRATION TESTS - check the database layer (validation + SQLite together)."""
from datetime import date, timedelta

import pytest

TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


def add_sample_patient(db, name="Ravi Teja"):
    return db.add_patient(name, 30, "Male", "9876543210", "Fever")


def add_sample_doctor(db, name="Dr. Priya Sharma"):
    return db.add_doctor(name, "Pediatrician", "9876501234", 400)


def test_default_admin_can_login(db):
    assert db.check_login("admin", "admin123") is True


def test_wrong_password_cannot_login(db):
    assert db.check_login("admin", "wrong") is False


def test_add_and_get_patient(db):
    patient_id = add_sample_patient(db)
    patient = db.get_patient(patient_id)
    assert patient["name"] == "Ravi Teja"
    assert patient["age"] == 30


def test_invalid_patient_is_not_saved(db):
    with pytest.raises(ValueError):
        db.add_patient("Ravi", 30, "Male", "123", "Fever")
    assert db.get_patients() == []


def test_search_patient_by_name(db):
    add_sample_patient(db, "Ravi Teja")
    add_sample_patient(db, "Sita Devi")
    results = db.get_patients(search="sita")
    assert [p["name"] for p in results] == ["Sita Devi"]


def test_search_patient_by_id(db):
    add_sample_patient(db, "Ravi Teja")
    sita_id = add_sample_patient(db, "Sita Devi")
    results = db.get_patients(search=str(sita_id))
    assert [p["name"] for p in results] == ["Sita Devi"]


def test_update_patient(db):
    patient_id = add_sample_patient(db)
    db.update_patient(patient_id, "Ravi Teja", 31, "Male", "9000000001", "Cold")
    patient = db.get_patient(patient_id)
    assert (patient["age"], patient["phone"], patient["disease"]) == (31, "9000000001", "Cold")


def test_update_patient_with_invalid_age_keeps_old_data(db):
    patient_id = add_sample_patient(db)
    with pytest.raises(ValueError):
        db.update_patient(patient_id, "Ravi Teja", 200, "Male", "9876543210", "Fever")
    assert db.get_patient(patient_id)["age"] == 30


def test_delete_patient(db):
    patient_id = add_sample_patient(db)
    db.delete_patient(patient_id)
    assert db.get_patient(patient_id) is None


def test_update_doctor(db):
    d = add_sample_doctor(db)
    db.update_doctor(d, "Dr. Priya Sharma", "Neonatologist", "9876501234", 600)
    doctor = db.get_doctor(d)
    assert (doctor["specialization"], doctor["fee"]) == ("Neonatologist", 600)


def test_search_doctor_by_specialization(db):
    add_sample_doctor(db, "Dr. Priya Sharma")
    db.add_doctor("Dr. Anil Reddy", "Orthopedic", "9123456780", 450)
    results = db.get_doctors(search="ortho")
    assert [d["name"] for d in results] == ["Dr. Anil Reddy"]


def test_unavailable_doctor_cannot_be_booked(db):
    p = add_sample_patient(db)
    d = add_sample_doctor(db)
    db.toggle_availability(d)
    assert db.get_doctor(d)["available"] == 0
    with pytest.raises(ValueError, match="not available"):
        db.book_appointment(p, d, TOMORROW, "10:00")


def test_book_appointment(db):
    p = add_sample_patient(db)
    d = add_sample_doctor(db)
    db.book_appointment(p, d, TOMORROW, "10:00")
    appointments = db.get_appointments()
    assert len(appointments) == 1
    assert appointments[0]["status"] == "Scheduled"


def test_doctor_cannot_be_double_booked(db):
    p1 = add_sample_patient(db, "Ravi Teja")
    p2 = add_sample_patient(db, "Sita Devi")
    d = add_sample_doctor(db)
    db.book_appointment(p1, d, TOMORROW, "10:00")
    with pytest.raises(ValueError, match="already booked"):
        db.book_appointment(p2, d, TOMORROW, "10:00")


def test_slot_is_free_again_after_cancel(db):
    p = add_sample_patient(db)
    d = add_sample_doctor(db)
    appt = db.book_appointment(p, d, TOMORROW, "10:00")
    db.cancel_appointment(appt)
    db.book_appointment(p, d, TOMORROW, "10:00")  # should not raise
    assert len(db.get_appointments()) == 2


def test_appointment_needs_existing_patient(db):
    d = add_sample_doctor(db)
    with pytest.raises(ValueError, match="valid patient"):
        db.book_appointment(999, d, TOMORROW, "10:00")


def test_medical_record_history(db):
    p = add_sample_patient(db)
    db.add_medical_record(p, "2026-01-10", "Viral fever", "Rest", "Paracetamol")
    db.add_medical_record(p, "2026-03-05", "Sprained ankle", "Bandage", "Ibuprofen")
    history = db.get_medical_records(p)
    assert [r["diagnosis"] for r in history] == ["Sprained ankle", "Viral fever"]  # newest first


def test_medical_record_needs_diagnosis(db):
    p = add_sample_patient(db)
    with pytest.raises(ValueError, match="Diagnosis"):
        db.add_medical_record(p, TODAY, "", "Rest", "Paracetamol")


def test_bill_with_zero_total_is_rejected(db):
    p = add_sample_patient(db)
    with pytest.raises(ValueError, match="greater than 0"):
        db.create_bill(p, 0, 0)


def test_create_bill_and_mark_paid(db):
    p = add_sample_patient(db)
    bill_id = db.create_bill(p, 500, 1200)
    bill = db.get_bills()[0]
    assert bill["total"] == 1700  # consultation + treatment
    assert bill["status"] == "Unpaid"
    db.mark_bill_paid(bill_id)
    assert db.get_bills()[0]["status"] == "Paid"


def test_deleting_patient_removes_their_appointments_and_bills(db):
    p = add_sample_patient(db)
    d = add_sample_doctor(db)
    db.book_appointment(p, d, TOMORROW, "10:00")
    db.create_bill(p, 400, 0)
    db.delete_patient(p)
    assert db.get_appointments() == []
    assert db.get_bills() == []


def test_dashboard_stats(db):
    p = add_sample_patient(db)
    d = add_sample_doctor(db)
    db.book_appointment(p, d, TOMORROW, "11:00")
    db.create_bill(p, 400, 0)
    db.add_medical_record(p, TODAY, "Viral fever", "Rest and fluids", "Paracetamol 500mg")
    assert db.get_stats() == {"patients": 1, "doctors": 1, "appointments": 1,
                              "records": 1, "unpaid_bills": 1}
