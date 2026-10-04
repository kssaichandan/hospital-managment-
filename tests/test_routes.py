"""FUNCTIONAL TESTS - send real HTTP requests to the Flask app (no browser)."""
from datetime import date, timedelta

TOMORROW = (date.today() + timedelta(days=1)).isoformat()

PATIENT = {"name": "Ravi Teja", "age": "30", "gender": "Male",
           "phone": "9876543210", "disease": "Fever"}
DOCTOR = {"name": "Dr. Priya Sharma", "specialization": "Pediatrician",
          "phone": "9876501234", "fee": "400"}


def test_login_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_with_correct_password(client):
    response = client.post("/", data={"username": "admin", "password": "admin123"},
                           follow_redirects=True)
    assert b"Dashboard" in response.data


def test_login_with_wrong_password(client):
    response = client.post("/", data={"username": "admin", "password": "nope"},
                           follow_redirects=True)
    assert b"Invalid username or password" in response.data


def test_pages_are_protected_without_login(client):
    for page in ["/dashboard", "/patients", "/doctors", "/appointments", "/records", "/billing"]:
        response = client.get(page)
        assert response.status_code == 302  # redirected to login
        assert response.headers["Location"] == "/"


def test_add_patient(logged_in_client):
    response = logged_in_client.post("/patients", data=PATIENT, follow_redirects=True)
    assert b"Patient added successfully" in response.data
    assert b"Ravi Teja" in response.data


def test_add_patient_with_invalid_phone_shows_error(logged_in_client):
    bad = dict(PATIENT, phone="12345")
    response = logged_in_client.post("/patients", data=bad, follow_redirects=True)
    assert b"Phone number must be exactly 10 digits" in response.data
    assert b"No patients found" in response.data


def test_empty_patient_form_shows_validation_message(logged_in_client):
    empty = {"name": "", "age": "", "gender": "Male", "phone": "", "disease": ""}
    response = logged_in_client.post("/patients", data=empty, follow_redirects=True)
    assert b"Name must have at least 2 characters" in response.data


def test_update_patient(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    changed = dict(PATIENT, disease="Typhoid")
    response = logged_in_client.post("/patients/1/edit", data=changed, follow_redirects=True)
    assert b"Patient details updated successfully" in response.data
    assert b"Typhoid" in response.data


def test_search_patient_by_id(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    logged_in_client.post("/patients", data=dict(PATIENT, name="Sita Devi"))
    response = logged_in_client.get("/patients?search=2")
    assert b"Sita Devi" in response.data
    assert b"Ravi Teja" not in response.data


def test_delete_patient(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    response = logged_in_client.post("/patients/1/delete", follow_redirects=True)
    assert b"Patient removed successfully" in response.data
    assert b"Ravi Teja" not in response.data


def test_add_doctor(logged_in_client):
    response = logged_in_client.post("/doctors", data=DOCTOR, follow_redirects=True)
    assert b"Doctor added successfully" in response.data
    assert b"Pediatrician" in response.data


def test_update_doctor_and_toggle_availability(logged_in_client):
    logged_in_client.post("/doctors", data=DOCTOR)
    response = logged_in_client.post("/doctors/1/edit", data=dict(DOCTOR, fee="650"),
                                     follow_redirects=True)
    assert b"650.00" in response.data
    response = logged_in_client.post("/doctors/1/availability", follow_redirects=True)
    assert b"Not Available" in response.data


def test_add_medical_record(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    response = logged_in_client.post(
        "/records",
        data={"patient_id": "1", "visit_date": date.today().isoformat(),
              "diagnosis": "Viral fever", "treatment": "Rest", "prescription": "Paracetamol"},
        follow_redirects=True,
    )
    assert b"Medical record saved successfully" in response.data
    assert b"Viral fever" in response.data


def test_book_appointment_and_cancel(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    logged_in_client.post("/doctors", data=DOCTOR)
    response = logged_in_client.post(
        "/appointments",
        data={"patient_id": "1", "doctor_id": "1", "date": TOMORROW, "time": "10:00"},
        follow_redirects=True,
    )
    assert b"Appointment booked successfully" in response.data
    response = logged_in_client.post("/appointments/1/cancel", follow_redirects=True)
    assert b"Cancelled" in response.data


def test_create_and_pay_bill(logged_in_client):
    logged_in_client.post("/patients", data=PATIENT)
    response = logged_in_client.post(
        "/billing", data={"patient_id": "1", "consultation_charge": "500",
                          "treatment_charge": "1200"},
        follow_redirects=True,
    )
    assert b"Bill generated successfully" in response.data
    assert b"1700.00" in response.data
    response = logged_in_client.post("/billing/1/pay", follow_redirects=True)
    assert b"Bill marked as paid" in response.data


def test_logout(logged_in_client):
    logged_in_client.get("/logout")
    assert logged_in_client.get("/dashboard").status_code == 302
