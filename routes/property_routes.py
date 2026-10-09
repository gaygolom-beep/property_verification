from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from extensions import db
from models import Property, VerificationRecord
from routes.geocoding import geocode_address

property_bp = Blueprint("property", __name__, url_prefix="/properties")


def _read_location_fields(form):
    """Pull the location sub-fields out of a submitted form."""
    return {
        "locality": form.get("locality", "").strip() or None,
        "city": form.get("city", "").strip() or None,
        "state": form.get("state", "").strip() or None,
        "pincode": form.get("pincode", "").strip() or None,
    }


def _geocode_property(prop):
    """
    Best-effort geocode of a property's full address. Never raises -- if the
    lookup fails (no network, address not recognized, etc.) the property is
    still saved, just without coordinates, and the map falls back to an
    address-based "Open in Google Maps" link instead of an embedded marker.
    """
    lat, lon = geocode_address(prop.full_address)
    prop.latitude = lat
    prop.longitude = lon


def _get_owned_or_admin(property_id):
    """Fetch a property, enforcing that a plain user can only touch their own."""
    prop = Property.query.get_or_404(property_id)
    if not current_user.is_admin and prop.owner_id != current_user.id:
        abort(403)
    return prop


@property_bp.route("/")
@login_required
def list_properties():
    status_filter = request.args.get("status", "")
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    query = Property.query if current_user.is_admin else Property.query.filter_by(owner_id=current_user.id)
    if status_filter:
        query = query.filter_by(overall_status=status_filter)
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(
            db.or_(Property.title.ilike(like), Property.address.ilike(like), Property.city.ilike(like))
        )

    pagination = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template(
        "property/list.html",
        properties=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        search_query=search_query,
        status_choices=Property.STATUS_CHOICES,
    )


@property_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_property():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        property_type = request.form.get("property_type", "").strip()
        survey_number = request.form.get("survey_number", "").strip()
        address = request.form.get("address", "").strip()
        area_sq_ft = request.form.get("area_sq_ft", "").strip()

        if not title or not property_type or not address:
            flash("Title, property type and address are required.", "danger")
            return redirect(url_for("property.new_property"))

        prop = Property(
            owner_id=current_user.id,
            title=title,
            property_type=property_type,
            survey_number=survey_number or None,
            address=address,
            area_sq_ft=float(area_sq_ft) if area_sq_ft else None,
            overall_status="Pending",
            **_read_location_fields(request.form),
        )
        _geocode_property(prop)
        db.session.add(prop)
        db.session.flush()  # get prop.id before commit

        # Seed the audit trail with the initial status
        db.session.add(
            VerificationRecord(
                property_id=prop.id,
                changed_by_id=current_user.id,
                status="Pending",
                remarks="Property created and submitted for verification.",
            )
        )
        db.session.commit()

        flash("Property added successfully.", "success")
        return redirect(url_for("property.view_property", property_id=prop.id))

    return render_template("property/form.html", property=None)


@property_bp.route("/<int:property_id>")
@login_required
def view_property(property_id):
    prop = _get_owned_or_admin(property_id)

    # Existing properties saved before the map feature (or ones whose first
    # geocode attempt failed) won't have coordinates yet. Make one best-effort
    # lookup on view so they self-heal without anyone having to re-save the
    # form; if it still fails, the template falls back to an address-based
    # "Open in Google Maps" link instead of an embedded marker.
    if not prop.has_coordinates and prop.full_address:
        _geocode_property(prop)
        db.session.commit()

    return render_template("property/detail.html", property=prop)


@property_bp.route("/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
def edit_property(property_id):
    prop = _get_owned_or_admin(property_id)

    if request.method == "POST":
        prop.title = request.form.get("title", "").strip()
        prop.property_type = request.form.get("property_type", "").strip()
        prop.survey_number = request.form.get("survey_number", "").strip() or None
        new_address = request.form.get("address", "").strip()
        area_sq_ft = request.form.get("area_sq_ft", "").strip()
        prop.area_sq_ft = float(area_sq_ft) if area_sq_ft else None

        location_fields = _read_location_fields(request.form)
        address_or_location_changed = (
            new_address != prop.address
            or location_fields["locality"] != prop.locality
            or location_fields["city"] != prop.city
            or location_fields["state"] != prop.state
            or location_fields["pincode"] != prop.pincode
        )

        prop.address = new_address
        for field_name, value in location_fields.items():
            setattr(prop, field_name, value)

        # Only re-geocode when the address actually changed -- avoids an
        # unnecessary lookup (and Nominatim request) on every unrelated edit.
        if address_or_location_changed:
            _geocode_property(prop)

        db.session.commit()
        flash("Property updated.", "success")
        return redirect(url_for("property.view_property", property_id=prop.id))

    return render_template("property/form.html", property=prop)


@property_bp.route("/<int:property_id>/delete", methods=["POST"])
@login_required
def delete_property(property_id):
    prop = _get_owned_or_admin(property_id)
    db.session.delete(prop)
    db.session.commit()
    flash("Property deleted.", "info")
    return redirect(url_for("property.list_properties"))
