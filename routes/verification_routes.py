from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from extensions import db
from models import Property, VerificationRecord
from routes.notifications import send_status_change_email

verification_bp = Blueprint("verification", __name__, url_prefix="/verification")


@verification_bp.route("/property/<int:property_id>")
@login_required
def history(property_id):
    prop = Property.query.get_or_404(property_id)
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)

    records = (
        VerificationRecord.query.filter_by(property_id=property_id)
        .order_by(VerificationRecord.created_at.desc())
        .all()
    )
    return render_template("verification/history.html", property=prop, records=records)


@verification_bp.route("/property/<int:property_id>/update", methods=["POST"])
@login_required
def update_status(property_id):
    # Only admins (verification officers) can change verification status --
    # this is the "human review boundary" from the project's Innovative Work
    # slide: AI/automation informs the decision, a person makes it.
    if not current_user.is_admin:
        abort(403)

    prop = Property.query.get_or_404(property_id)
    new_status = request.form.get("status", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if new_status not in Property.STATUS_CHOICES:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("verification.history", property_id=property_id))

    prop.overall_status = new_status
    db.session.add(
        VerificationRecord(
            property_id=prop.id,
            changed_by_id=current_user.id,
            status=new_status,
            remarks=remarks or None,
        )
    )
    db.session.commit()
    send_status_change_email(prop, new_status, remarks)

    flash(f"Verification status updated to '{new_status}'.", "success")
    return redirect(url_for("verification.history", property_id=property_id))
