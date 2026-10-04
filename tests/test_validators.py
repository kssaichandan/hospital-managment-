"""UNIT TESTS - check each validation rule on its own."""
from datetime import date

import pytest

import validators as v


@pytest.mark.parametrize("phone", ["9876543210", "0123456789"])
def test_valid_phone_is_accepted(phone):
    assert v.validate_phone(phone) == phone


@pytest.mark.parametrize("phone", ["12345", "98765432101", "98765abcde", ""])
def test_invalid_phone_is_rejected(phone):
    with pytest.raises(ValueError, match="10 digits"):
        v.validate_phone(phone)


@pytest.mark.parametrize("age", [0, 25, 120, "45"])
def test_valid_age_is_accepted(age):
    assert v.validate_age(age) == int(age)


@pytest.mark.parametrize("age", [-1, 121, 500])
def test_age_out_of_range_is_rejected(age):
    with pytest.raises(ValueError, match="between 0 and 120"):
        v.validate_age(age)


def test_age_must_be_a_number():
    with pytest.raises(ValueError, match="must be a number"):
        v.validate_age("twenty")


def test_valid_name_is_trimmed():
    assert v.validate_name("  Ravi Teja  ") == "Ravi Teja"


@pytest.mark.parametrize("name", ["", "A", "Ravi123", "R@vi"])
def test_invalid_name_is_rejected(name):
    with pytest.raises(ValueError):
        v.validate_name(name)


def test_invalid_gender_is_rejected():
    with pytest.raises(ValueError, match="Gender"):
        v.validate_gender("Unknown")


@pytest.mark.parametrize("amount", [0, -100, "abc"])
def test_invalid_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        v.validate_amount(amount)


def test_past_appointment_date_is_rejected():
    with pytest.raises(ValueError, match="past"):
        v.validate_appointment_date("2020-01-01", today=date(2026, 1, 1))


def test_today_is_a_valid_appointment_date():
    assert v.validate_appointment_date("2026-01-01", today=date(2026, 1, 1)) == "2026-01-01"


def test_wrong_date_format_is_rejected():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        v.validate_appointment_date("01/01/2026")


def test_invalid_time_slot_is_rejected():
    with pytest.raises(ValueError, match="time slot"):
        v.validate_time_slot("13:00")  # lunch break, not a slot


def test_zero_treatment_charge_is_allowed():
    assert v.validate_charge("0", "Treatment charge") == 0


def test_negative_charge_is_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        v.validate_charge(-50, "Treatment charge")


def test_future_visit_date_is_rejected():
    with pytest.raises(ValueError, match="future"):
        v.validate_visit_date("2026-12-31", today=date(2026, 1, 1))


# ---- regression tests for bugs found during exploratory (break) testing ----
@pytest.mark.parametrize("name", ["..", "''", ". ."])
def test_name_with_only_symbols_is_rejected(name):
    with pytest.raises(ValueError, match="at least 2 letters"):
        v.validate_name(name)


def test_very_long_name_is_rejected():
    with pytest.raises(ValueError, match="longer than 50"):
        v.validate_name("A" * 51)


def test_very_long_text_is_rejected():
    with pytest.raises(ValueError, match="longer than 200"):
        v.validate_text("x" * 201, "Disease")


@pytest.mark.parametrize("amount", ["nan", "inf", "1e309"])
def test_nan_and_infinity_amounts_are_rejected(amount):
    with pytest.raises(ValueError, match="must be a number"):
        v.validate_amount(amount)
    with pytest.raises(ValueError, match="must be a number"):
        v.validate_charge(amount, "Treatment charge")


def test_phone_with_non_english_digits_is_rejected():
    with pytest.raises(ValueError, match="10 digits"):
        v.validate_phone("９８７６５４３２１０")  # full-width digits
