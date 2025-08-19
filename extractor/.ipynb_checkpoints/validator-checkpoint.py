# extractor/validator.py
import re
from dateutil.parser import parse as dateparse

def is_currency(s: str) -> bool:
    try:
        float(str(s).replace(",", "").replace("$", "").strip())
        return True
    except Exception:
        return False

def is_date(s: str) -> bool:
    try:
        dateparse(s, fuzzy=True)
        return True
    except Exception:
        return False

def validate_invoice_fields(fields: dict, line_items: list):
    passed, failed, notes = [], [], []

    # InvoiceNumber regex
    if re.match(r"^(INV[-/]?\d+|\d+)$", str(fields.get("InvoiceNumber", "")), re.I):
        passed.append("invoice_number_format")
    else:
        failed.append("invoice_number_format")

    # InvoiceDate validity
    if is_date(fields.get("InvoiceDate", "")):
        passed.append("invoice_date_valid")
    else:
        failed.append("invoice_date_valid")

    # TotalAmount currency
    if is_currency(fields.get("TotalAmount", "")):
        passed.append("total_amount_currency")
    else:
        failed.append("total_amount_currency")

    # Totals check
    try:
        total = float(fields.get("TotalAmount", "0").replace(",", ""))
    except Exception:
        total = None
    sum_lines = 0.0
    for li in line_items or []:
        try:
            sum_lines += float(li.get("amount", 0))
        except Exception:
            pass
    if total is not None:
        if abs(total - sum_lines) < 1.0:  # tolerance
            passed.append("totals_match")
        else:
            failed.append("totals_match")
            notes.append(f"total={total} sum_line_items={sum_lines}")

    return {"passed_rules": passed, "failed_rules": failed, "notes": ";".join(notes)}

def validate_medical_bill(fields: dict, line_items: list):
    passed, failed, notes = [], [], []

    # PatientName required
    if fields.get("PatientName"):
        passed.append("patient_name_present")
    else:
        failed.append("patient_name_present")

    # PatientID alphanumeric
    if re.match(r"^[A-Za-z0-9\-]+$", str(fields.get("PatientID", ""))):
        passed.append("patient_id_format")
    else:
        failed.append("patient_id_format")

    # Admission < Discharge
    try:
        adm = dateparse(fields.get("AdmissionDate", ""))
        dis = dateparse(fields.get("DischargeDate", ""))
        if adm < dis:
            passed.append("admission_before_discharge")
        else:
            failed.append("admission_before_discharge")
    except Exception:
        failed.append("admission_before_discharge")

    # TotalAmount vs line_items
    try:
        total = float(fields.get("TotalAmount", "0").replace(",", ""))
    except Exception:
        total = None
    sum_lines = 0.0
    for li in line_items or []:
        try:
            sum_lines += float(li.get("amount", 0))
        except Exception:
            pass
    if total is not None:
        if abs(total - sum_lines) < 1.0:
            passed.append("totals_match")
        else:
            failed.append("totals_match")
            notes.append(f"total={total} sum_line_items={sum_lines}")

    return {"passed_rules": passed, "failed_rules": failed, "notes": ";".join(notes)}

def validate_prescription(fields: dict, line_items: list):
    passed, failed, notes = [], [], []

    # Required names
    if fields.get("PatientName"):
        passed.append("patient_name_present")
    else:
        failed.append("patient_name_present")

    if fields.get("DoctorName"):
        passed.append("doctor_name_present")
    else:
        failed.append("doctor_name_present")

    # PrescriptionDate validity
    if is_date(fields.get("PrescriptionDate", "")):
        passed.append("prescription_date_valid")
    else:
        failed.append("prescription_date_valid")

    # Medications list not empty
    if line_items and len(line_items) > 0:
        passed.append("medications_present")
    else:
        failed.append("medications_present")

    # Each medication dosage format
    for li in line_items or []:
        dose = li.get("description", "")
        if re.search(r"\b\d+(mg|ml|mcg)\b", str(dose).lower()):
            passed.append("dosage_format")
        else:
            failed.append("dosage_format")

    return {"passed_rules": passed, "failed_rules": failed, "notes": ";".join(notes)}

def validate_fields(doc_type: str, fields: dict, line_items: list):
    if doc_type == "invoice":
        return validate_invoice_fields(fields, line_items)
    elif doc_type == "medical_bill":
        return validate_medical_bill(fields, line_items)
    elif doc_type == "prescription":
        return validate_prescription(fields, line_items)
    else:
        return {"passed_rules": [], "failed_rules": [], "notes": "unknown doc_type"}
