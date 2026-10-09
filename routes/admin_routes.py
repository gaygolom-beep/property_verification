import csv
import io

from flask import Blueprint, render_template, abort, Response
from flask_login import login_required, current_user

from extensions import db
from models import Property, Document, User, AnalysisResult

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not current_user.is_admin:
        abort(403)


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    _require_admin()

    total_properties = Property.query.count()
    total_documents = Document.query.count()

    # Count every distinct property owner, not just role == "user" -- an
    # admin account that also owns test properties (e.g. the first
    # registered account) was previously left out of this count entirely.
    total_owners = db.session.query(Property.owner_id).distinct().count()

    status_counts = {
        status: Property.query.filter_by(overall_status=status).count()
        for status in Property.STATUS_CHOICES
    }

    ocr_counts = {
        status: Document.query.filter_by(ocr_status=status).count()
        for status in Document.OCR_STATUS_CHOICES
    }

    # OCR accuracy proxy: share of processed documents that came back
    # Completed rather than Failed (Not Processed/Processing excluded, since
    # those haven't run yet and aren't a success/failure outcome).
    processed = ocr_counts.get("Completed", 0) + ocr_counts.get("Failed", 0)
    ocr_success_rate = round((ocr_counts.get("Completed", 0) / processed) * 100, 1) if processed else None

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    analyzed_property_ids = set()
    for prop in Property.query.all():
        latest = prop.latest_analysis
        if latest:
            risk_counts[latest.risk_level] = risk_counts.get(latest.risk_level, 0) + 1
            analyzed_property_ids.add(prop.id)

    total_analyses = AnalysisResult.query.count()
    properties_analyzed = len(analyzed_property_ids)
    properties_awaiting_analysis = total_properties - properties_analyzed

    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(10).all()

    review_queue_count = Property.query.filter(
        Property.overall_status.in_(["Pending", "In Review"])
    ).count()

    return render_template(
        "admin/dashboard.html",
        total_properties=total_properties,
        total_documents=total_documents,
        total_owners=total_owners,
        status_counts=status_counts,
        ocr_counts=ocr_counts,
        ocr_success_rate=ocr_success_rate,
        risk_counts=risk_counts,
        total_analyses=total_analyses,
        properties_analyzed=properties_analyzed,
        properties_awaiting_analysis=properties_awaiting_analysis,
        review_queue_count=review_queue_count,
        recent_properties=recent_properties,
    )


@admin_bp.route("/dashboard/export.csv")
@login_required
def export_dashboard_csv():
    """All properties with their current status, risk, and document counts."""
    _require_admin()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Property", "Type", "Owner", "Status", "Risk Level", "Risk Score", "Documents", "Created"])
    for p in Property.query.order_by(Property.created_at.desc()).all():
        latest = p.latest_analysis
        writer.writerow([
            p.title, p.property_type, p.owner.full_name, p.overall_status,
            latest.risk_level if latest else "Not analyzed",
            latest.risk_score if latest else "",
            len(p.documents), p.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=properties_summary.csv"},
    )
