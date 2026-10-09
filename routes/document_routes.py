import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Property, Document
from routes.ocr import extract_text_from_file

document_bp = Blueprint("document", __name__, url_prefix="/documents")


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _get_property_for_user(property_id):
    prop = Property.query.get_or_404(property_id)
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return prop


@document_bp.route("/property/<int:property_id>/upload", methods=["GET", "POST"])
@login_required
def upload_document(property_id):
    prop = _get_property_for_user(property_id)

    if request.method == "POST":
        doc_type = request.form.get("doc_type", "").strip()
        file = request.files.get("file")

        if not doc_type:
            flash("Please choose a document type.", "danger")
            return redirect(url_for("document.upload_document", property_id=property_id))

        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return redirect(url_for("document.upload_document", property_id=property_id))

        if not _allowed_file(file.filename):
            flash("Unsupported file type. Allowed: PDF, PNG, JPG, JPEG.", "danger")
            return redirect(url_for("document.upload_document", property_id=property_id))

        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit(".", 1)[-1].lower()
        stored_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename)
        file.save(filepath)

        document = Document(
            property_id=prop.id,
            doc_type=doc_type,
            original_filename=original_filename,
            stored_filename=stored_filename,
            ocr_status="Processing",
        )
        db.session.add(document)
        db.session.commit()

        # Run OCR synchronously for simplicity in this phase. Moving this to
        # a background task queue (e.g. Celery/RQ) is a good Phase-2
        # scalability improvement once volume grows.
        status, text = extract_text_from_file(filepath)
        document.ocr_status = status
        document.extracted_text = text
        db.session.commit()

        flash(f"Document uploaded. OCR status: {status}.", "success")
        return redirect(url_for("property.view_property", property_id=property_id))

    return render_template("document/upload.html", property=prop, doc_types=Document.DOC_TYPES)


@document_bp.route("/<int:document_id>/file")
@login_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    prop = document.property
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], document.stored_filename, as_attachment=False
    )


@document_bp.route("/<int:document_id>/reprocess-ocr", methods=["POST"])
@login_required
def reprocess_ocr(document_id):
    document = Document.query.get_or_404(document_id)
    prop = document.property
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], document.stored_filename)
    status, text = extract_text_from_file(filepath)
    document.ocr_status = status
    document.extracted_text = text
    db.session.commit()

    flash(f"OCR re-run complete. Status: {status}.", "info")
    return redirect(url_for("property.view_property", property_id=prop.id))


@document_bp.route("/<int:document_id>/delete", methods=["POST"])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    prop = document.property
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], document.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    property_id = prop.id
    db.session.delete(document)
    db.session.commit()

    flash("Document deleted.", "info")
    return redirect(url_for("property.view_property", property_id=property_id))
