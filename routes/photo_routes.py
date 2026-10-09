import os
import uuid

from flask import Blueprint, redirect, url_for, flash, request, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Property, PropertyPhoto

photo_bp = Blueprint("photo", __name__, url_prefix="/photos")

ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _get_property_for_user(property_id):
    prop = Property.query.get_or_404(property_id)
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return prop


@photo_bp.route("/<int:photo_id>/file")
@login_required
def serve_photo(photo_id):
    photo = PropertyPhoto.query.get_or_404(photo_id)
    prop = photo.property
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], photo.stored_filename)


@photo_bp.route("/property/<int:property_id>/upload", methods=["POST"])
@login_required
def upload_photos(property_id):
    prop = _get_property_for_user(property_id)
    files = [f for f in request.files.getlist("photos") if f and f.filename]

    if not files:
        flash("Choose at least one photo to upload.", "danger")
        return redirect(url_for("property.view_property", property_id=property_id))

    next_order = len(prop.photos)
    saved = 0
    for i, file in enumerate(files[:10]):  # cap per-request to keep things sane
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_PHOTO_EXTENSIONS:
            continue
        original_filename = secure_filename(file.filename)
        stored_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename)
        file.save(filepath)

        db.session.add(PropertyPhoto(
            property_id=prop.id, stored_filename=stored_filename,
            original_filename=original_filename, sort_order=next_order + i,
        ))
        saved += 1

    db.session.commit()
    if saved:
        flash(f"{saved} photo(s) uploaded.", "success")
    else:
        flash("No valid image files found (allowed: PNG, JPG, JPEG, WEBP).", "danger")
    return redirect(url_for("property.view_property", property_id=property_id))


@photo_bp.route("/<int:photo_id>/delete", methods=["POST"])
@login_required
def delete_photo(photo_id):
    photo = PropertyPhoto.query.get_or_404(photo_id)
    prop = photo.property
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    property_id = prop.id
    db.session.delete(photo)
    db.session.commit()
    flash("Photo removed.", "info")
    return redirect(url_for("property.view_property", property_id=property_id))
