import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """
    A platform user. role is either 'user' (property owner / uploader)
    or 'admin' (verification officer who reviews properties and documents).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    properties = db.relationship("Property", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Property(db.Model):
    """
    A property record submitted for verification.
    overall_status mirrors the latest VerificationRecord for quick listing/filtering.
    """

    __tablename__ = "properties"

    STATUS_CHOICES = ["Pending", "In Review", "Verified", "Rejected"]

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # Residential/Commercial/Agricultural/Other
    survey_number = db.Column(db.String(80))
    address = db.Column(db.String(300), nullable=False)
    area_sq_ft = db.Column(db.Float)

    # Location fields (added for the Property Location Map feature).
    # All nullable/optional so existing rows created before this feature
    # keep working exactly as before -- they just show "not mapped yet"
    # until someone edits them or a geocode lookup succeeds.
    locality = db.Column(db.String(120))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    pincode = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    overall_status = db.Column(db.String(20), nullable=False, default="Pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = db.relationship("Document", backref="property", lazy=True, cascade="all, delete-orphan")
    photos = db.relationship(
        "PropertyPhoto",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="PropertyPhoto.sort_order",
    )
    analyses = db.relationship(
        "AnalysisResult",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="AnalysisResult.created_at",
    )
    verification_records = db.relationship(
        "VerificationRecord",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="VerificationRecord.created_at",
    )

    @property
    def latest_analysis(self):
        return self.analyses[-1] if self.analyses else None

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def full_address(self):
        """Address plus any locality/city/state/pincode parts that are set."""
        parts = [self.address, self.locality, self.city, self.state, self.pincode]
        return ", ".join(p.strip() for p in parts if p and p.strip())

    def __repr__(self):
        return f"<Property {self.title} [{self.overall_status}]>"


class Document(db.Model):
    """
    An uploaded supporting document for a property (title deed, NOC, tax
    receipt, etc). extracted_text / ocr_status are populated by the OCR module
    and are the hand-off point for the future NLP consistency-checking module.
    """

    __tablename__ = "documents"

    DOC_TYPES = ["Title Deed", "NOC", "Tax Receipt", "Sale Agreement", "Other"]
    OCR_STATUS_CHOICES = ["Not Processed", "Processing", "Completed", "Failed"]

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    doc_type = db.Column(db.String(50), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)

    ocr_status = db.Column(db.String(20), nullable=False, default="Not Processed")
    extracted_text = db.Column(db.Text)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document {self.original_filename} ({self.doc_type})>"


class VerificationRecord(db.Model):
    """
    Append-only audit trail entry for a property's verification status.
    A new row is added every time status changes -- rows are never edited or
    deleted, which preserves the audit history required by the project brief.
    """

    __tablename__ = "verification_records"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    status = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    changed_by = db.relationship("User")

    def __repr__(self):
        return f"<VerificationRecord property={self.property_id} status={self.status}>"


class AnalysisResult(db.Model):
    """
    Output of one automated verification run (NLP matching + risk scoring).
    A new row is stored for every run, so re-analysing after new documents
    are uploaded keeps the earlier results as history.
    """

    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    run_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(10), nullable=False)  # Low | Medium | High
    checks_run = db.Column(db.Integer, default=0)
    checks_passed = db.Column(db.Integer, default=0)

    findings_json = db.Column(db.Text, nullable=False, default="[]")
    fields_json = db.Column(db.Text, nullable=False, default="[]")
    features_json = db.Column(db.Text, nullable=False, default="{}")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    run_by = db.relationship("User")

    @property
    def findings(self):
        return json.loads(self.findings_json or "[]")

    @property
    def document_fields(self):
        return json.loads(self.fields_json or "[]")

    @property
    def features(self):
        return json.loads(self.features_json or "{}")

    def __repr__(self):
        return f"<AnalysisResult property={self.property_id} {self.risk_score} {self.risk_level}>"


class PropertyPhoto(db.Model):
    """A display photo of the property (not a legal document -- see Document)."""

    __tablename__ = "property_photos"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(160))
    sort_order = db.Column(db.Integer, default=0)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PropertyPhoto {self.original_filename}>"
