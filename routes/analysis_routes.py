import csv
import io
from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, send_file, Response
from flask_login import login_required, current_user

from extensions import db
from models import Property, AnalysisResult
from analysis.service import run_analysis
from analysis.report import build_report_pdf
from analysis.extractor import extract_fields
from analysis.risk import compute_risk
from scripts.demo_data import SCENARIOS

analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")


def _queue_candidates():
    """Shared by the Review Queue page and its CSV export."""
    candidates = (
        Property.query.filter(Property.overall_status.in_(["In Review", "Pending"]))
        .order_by(Property.updated_at.desc())
        .all()
    )

    def sort_key(p):
        latest = p.latest_analysis
        risk_rank = {"High": 0, "Medium": 1, "Low": 2}.get(latest.risk_level if latest else None, 3)
        return (risk_rank, -(latest.risk_score if latest else -1))

    candidates.sort(key=sort_key)
    return candidates


def _get_owned_or_admin(property_id):
    prop = Property.query.get_or_404(property_id)
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return prop


@analysis_bp.route("/property/<int:property_id>/run", methods=["POST"])
@login_required
def run(property_id):
    prop = _get_owned_or_admin(property_id)

    if not prop.documents:
        flash("Upload at least one document before running automated verification.", "warning")
        return redirect(url_for("property.view_property", property_id=property_id))

    run_analysis(prop, current_user)
    flash("Automated verification complete — see the results below.", "success")
    return redirect(url_for("property.view_property", property_id=property_id))


@analysis_bp.route("/property/<int:property_id>/report")
@login_required
def report(property_id):
    prop = _get_owned_or_admin(property_id)
    analysis = prop.latest_analysis

    if not analysis:
        flash("Run automated verification before downloading a report.", "warning")
        return redirect(url_for("property.view_property", property_id=property_id))

    pdf_buffer = build_report_pdf(prop, analysis)
    filename = f"verification-report-{prop.id}.pdf"
    return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


@analysis_bp.route("/queue")
@login_required
def review_queue():
    """Module 12: admin queue of properties awaiting human review, flagged first."""
    if not current_user.is_admin:
        abort(403)
    return render_template("analysis/queue.html", properties=_queue_candidates())


@analysis_bp.route("/queue/export.csv")
@login_required
def export_queue_csv():
    if not current_user.is_admin:
        abort(403)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Property", "Owner", "Status", "Risk Level", "Risk Score", "Documents", "Last Updated"])
    for p in _queue_candidates():
        latest = p.latest_analysis
        writer.writerow([
            p.title, p.owner.full_name, p.overall_status,
            latest.risk_level if latest else "Not analyzed",
            latest.risk_score if latest else "",
            len(p.documents), p.updated_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=review_queue.csv"},
    )


@analysis_bp.route("/evaluation")
@login_required
def evaluation():
    """
    Module evaluation / "model report card": runs the real risk engine
    against the known-answer scenarios in scripts/demo_data.py (the same
    ones scripts/seed_demo.py uses) and reports how many it scored
    correctly. This is the project's substitute for a labeled fraud
    dataset -- an honest, reproducible accuracy check rather than a claimed
    number with nothing behind it. Read-only: does not touch the database.
    """
    if not current_user.is_admin:
        abort(403)

    rows = []
    correct = 0
    for sc in SCENARIOS:
        docs = []
        for doc_type, text in sc["docs"]:
            docs.append({
                "doc_type": doc_type, "filename": f"{doc_type}.png",
                "ocr_status": "Completed", "text": text, "fields": extract_fields(text),
            })
        prop = {"survey_number": sc["survey_number"], "area_sq_ft": sc["area_sq_ft"], "pincode": sc["pincode"]}
        result = compute_risk(prop, docs, today=date.today())
        is_correct = result["level"] == sc["expect"]
        if is_correct:
            correct += 1
        rows.append({
            "title": sc["title"],
            "property_type": sc["property_type"],
            "expected": sc["expect"],
            "actual": result["level"],
            "score": result["score"],
            "correct": is_correct,
            "checks_passed": result["checks_passed"],
            "checks_run": result["checks_run"],
            "top_findings": [f["title"] for f in result["findings"] if f["points"] > 0][:3],
        })

    accuracy = round((correct / len(rows)) * 100, 1) if rows else None

    # Simple per-level breakdown (precision-ish: of the ones we predicted as
    # each level, how many were actually meant to be that level).
    level_breakdown = {}
    for level in ["Low", "Medium", "High"]:
        expected_count = sum(1 for r in rows if r["expected"] == level)
        correct_count = sum(1 for r in rows if r["expected"] == level and r["correct"])
        level_breakdown[level] = {"expected": expected_count, "correct": correct_count}

    return render_template(
        "analysis/evaluation.html",
        rows=rows, correct=correct, total=len(rows), accuracy=accuracy,
        level_breakdown=level_breakdown,
    )
