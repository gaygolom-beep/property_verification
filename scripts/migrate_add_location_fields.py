"""
One-time migration: adds the new location columns (locality, city, state,
pincode, latitude, longitude) to an EXISTING `properties` table.

Why this is needed: Flask-SQLAlchemy's db.create_all() only creates tables
that don't exist yet -- it will never ALTER a table that's already there.
If you're setting up the app fresh, you don't need this script at all;
db.create_all() (called automatically in app.py) already creates the table
with every column from the current models.py, including the new ones.

Only run this if you already had the app running before the map feature was
added and have a database with real property data in it that you want to
keep. It only ADDS columns -- it never drops or modifies existing data.

Usage:
    python scripts/migrate_add_location_fields.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text

from app import create_app
from extensions import db

NEW_COLUMNS = {
    "locality": "VARCHAR(120)",
    "city": "VARCHAR(80)",
    "state": "VARCHAR(80)",
    "pincode": "VARCHAR(20)",
    "latitude": "FLOAT",
    "longitude": "FLOAT",
}


def main():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        existing_columns = {col["name"] for col in inspector.get_columns("properties")}

        added = []
        for column_name, column_type in NEW_COLUMNS.items():
            if column_name in existing_columns:
                continue
            db.session.execute(
                text(f"ALTER TABLE properties ADD COLUMN {column_name} {column_type}")
            )
            added.append(column_name)

        db.session.commit()

        if added:
            print(f"Added columns to 'properties': {', '.join(added)}")
        else:
            print("Nothing to do -- all location columns already exist.")


if __name__ == "__main__":
    main()
