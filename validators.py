"""
Validation rules for the Hospital Management System.

Every function here checks user input and raises ValueError with a
friendly message when something is wrong. Keeping the rules in one
small file makes them easy to unit-test with PyTest.
"""
from datetime import date, datetime

GENDERS = ("Male", "Female", "Other")
TIME_SLOTS = ("09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00")


def validate_name(name):
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Name must have at least 2 characters.")
    if not all(ch.isalpha() or ch in " .'" for ch in name):
        raise ValueError("Name can only contain letters, spaces, dots and apostrophes.")
    return name


def validate_age(age):
    try:
        age = int(age)
    except (TypeError, ValueError):
        raise ValueError("Age must be a number.")
    if age < 0 or age > 120:
        raise ValueError("Age must be between 0 and 120.")
    return age


def validate_gender(gender):
    if gender not in GENDERS:
        raise ValueError("Gender must be Male, Female or Other.")
    return gender


def validate_phone(phone):
    phone = (phone or "").strip()
    if len(phone) != 10 or not phone.isdigit():
        raise ValueError("Phone number must be exactly 10 digits.")
    return phone


def validate_amount(amount, field="Amount"):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number.")
    if amount <= 0:
        raise ValueError(f"{field} must be greater than 0.")
    return round(amount, 2)


def validate_charge(amount, field):
    """Like validate_amount, but 0 is allowed (e.g. no treatment charge)."""
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number.")
    if amount < 0:
        raise ValueError(f"{field} cannot be negative.")
    return round(amount, 2)


def validate_visit_date(value, today=None):
    """Medical record date must be in YYYY-MM-DD format and not in the future."""
    try:
        day = datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    if day > (today or date.today()):
        raise ValueError("Visit date cannot be in the future.")
    return day.isoformat()


def validate_text(value, field):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{field} is required.")
    return value


def validate_appointment_date(value, today=None):
    """Date must be in YYYY-MM-DD format and must not be in the past."""
    try:
        day = datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    if day < (today or date.today()):
        raise ValueError("Appointment date cannot be in the past.")
    return day.isoformat()


def validate_time_slot(value):
    if value not in TIME_SLOTS:
        raise ValueError("Please choose a valid time slot.")
    return value
