"""
Glue between the pure analysis engine and the database (Modules 8-10).
"""
import json

from sqlalchemy import func

from extensions import db
from models import AnalysisResult, Property, VerificationRecord

from .extractor import extract_fields
from .risk import compute_risk
from routes.notifications import send_status_change_email


def _is_duplicate_claim(prop):
    """True if a different owner already registered the same survey number in the same city."""
    if not prop.survey_number:
        return False
    query = Property.query.filter(
        Property.id != prop.id,
        Property.owner_id != prop.owner_id,
        func.lower(Property.survey_number) == prop.survey_number.strip().lower(),
    )
    for other in query.all():
        if not prop.city or not other.city or prop.city.strip().lower() == other.city.strip().lower():
            return True
    return False


def run_analysis(prop, user):
    """Run extraction + matching + scoring for one property and store the result."""
    docs = []
    for d in prop.documents:
        docs.append({
            "doc_type": d.doc_type,
            "filename": d.original_filename,
            "ocr_status": d.ocr_status,
            "text": d.extracted_text or "",
            "fields": extract_fields(d.extracted_text),
        })

    result = compute_risk(
        {"survey_number": prop.survey_number, "area_sq_ft": prop.area_sq_ft, "pincode": prop.pincode},
        docs,
        duplicate_property=_is_duplicate_claim(prop),
    )

    record = AnalysisResult(
        property_id=prop.id,
        run_by_id=user.id,
        risk_score=result["score"],
        risk_level=result["level"],
        checks_run=result["checks_run"],
        checks_passed=result["checks_passed"],
        findings_json=json.dumps(result["findings"]),
        fields_json=json.dumps([
            {"doc_type": d["doc_type"], "filename": d["filename"], "ocr_status": d["ocr_status"], "fields": d["fields"]}
            for d in docs
        ]),
        features_json=json.dumps(result["features"]),
    )
    db.session.add(record)

    # An automated run moves a fresh submission into human review. It never
    # verifies or rejects anything on its own.
    status_changed = False
    if prop.overall_status == "Pending":
        prop.overall_status = "In Review"
        status_changed = True
        remarks = f"Automated analysis completed: risk {result['score']}/100 ({result['level']}). Awaiting human review."
        db.session.add(VerificationRecord(
            property_id=prop.id,
            changed_by_id=user.id,
            status="In Review",
            remarks=remarks,
        ))

    db.session.commit()
    if status_changed:
        send_status_change_email(prop, "In Review", remarks)
    return record
