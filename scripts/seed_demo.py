"""
Seeds demo data so the app can be explored immediately after setup: an
admin account, an owner account, three properties (matching the scenarios
tested in analysis/risk.py), their documents (pre-filled with OCR text, so
no Tesseract install is required just to see the AI features), five
generated demo photos on the flagship property, and one completed
automated-analysis run per property.

Safe to run multiple times -- it skips creating anything that already
exists (matched by email / property title).

Usage:
    python scripts/seed_demo.py
"""
import os
import shutil
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import User, Property, Document, PropertyPhoto
from analysis.service import run_analysis
from scripts.demo_data import SCENARIOS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_PHOTOS_DIR = os.path.join(BASE_DIR, "static", "demo_photos")

ADMIN_EMAIL = "admin@propverify.com"
ADMIN_PASSWORD = "Admin@123"
OWNER_EMAIL = "owner@propverify.com"
OWNER_PASSWORD = "Owner@123"


def get_or_create_user(email, full_name, password, role):
    user = User.query.filter_by(email=email).first()
    if user:
        return user, False
    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user, True


def make_placeholder_document_file(upload_folder):
    """A blank white PNG standing in for a scanned document -- the demo
    doesn't need a real scanned image since extracted_text is seeded
    directly to showcase the OCR/NLP/risk pipeline without requiring
    Tesseract to be installed just to explore the app."""
    from PIL import Image
    stored_filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(upload_folder, stored_filename)
    Image.new("RGB", (800, 1000), "#ffffff").save(filepath)
    return stored_filename


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        upload_folder = app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        admin, admin_new = get_or_create_user(ADMIN_EMAIL, "Verification Admin", ADMIN_PASSWORD, "admin")
        owner, owner_new = get_or_create_user(OWNER_EMAIL, "Om Gaygol", OWNER_PASSWORD, "user")
        db.session.commit()

        demo_photo_files = sorted(
            f for f in os.listdir(DEMO_PHOTOS_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ) if os.path.isdir(DEMO_PHOTOS_DIR) else []

        created_properties = 0
        for i, sc in enumerate(SCENARIOS):
            if Property.query.filter_by(title=sc["title"], owner_id=owner.id).first():
                continue  # already seeded

            prop = Property(
                owner_id=owner.id,
                title=sc["title"],
                property_type=sc["property_type"],
                survey_number=sc["survey_number"],
                address=sc["address"],
                locality=sc["locality"],
                city=sc["city"],
                state=sc["state"],
                pincode=sc["pincode"],
                area_sq_ft=sc["area_sq_ft"],
                latitude=sc["lat"],
                longitude=sc["lng"],
                overall_status="Pending",
            )
            db.session.add(prop)
            db.session.flush()

            for doc_type, text in sc["docs"]:
                stored = make_placeholder_document_file(upload_folder)
                db.session.add(Document(
                    property_id=prop.id,
                    doc_type=doc_type,
                    original_filename=f"{doc_type.replace(' ', '_')}.png",
                    stored_filename=stored,
                    ocr_status="Completed",
                    extracted_text=text,
                ))

            # Flagship property (index 0) gets the full 5-photo slideshow;
            # the others get one photo each, cycling through the set, so
            # every seeded property has at least a thumbnail.
            if demo_photo_files:
                photos_for_this = demo_photo_files if i == 0 else [demo_photo_files[i % len(demo_photo_files)]]
                for order, fname in enumerate(photos_for_this):
                    stored = f"{uuid.uuid4().hex}{os.path.splitext(fname)[1]}"
                    shutil.copyfile(os.path.join(DEMO_PHOTOS_DIR, fname), os.path.join(upload_folder, stored))
                    db.session.add(PropertyPhoto(
                        property_id=prop.id, stored_filename=stored,
                        original_filename=fname, sort_order=order,
                    ))

            db.session.commit()
            run_analysis(prop, admin)  # populates AnalysisResult + moves Pending -> In Review
            created_properties += 1

        print("Seed complete.")
        print(f"  Admin login : {ADMIN_EMAIL} / {ADMIN_PASSWORD}" + ("" if admin_new else " (already existed)"))
        print(f"  Owner login : {OWNER_EMAIL} / {OWNER_PASSWORD}" + ("" if owner_new else " (already existed)"))
        print(f"  Properties created this run: {created_properties}")


if __name__ == "__main__":
    seed()
