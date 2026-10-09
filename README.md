# AI-Based Property Document Verification — Complete (100%)

Flask + HTML/CSS/JS (Bootstrap) + SQL database. All planned modules are
implemented:

**Phase 1 (60%)**
1. **Auth Module** — registration/login, role-based access (`user` / `admin`)
2. **Property Management Module** — add / edit / delete / list properties
3. **Document Upload & Management Module** — upload title deeds, NOCs, etc.
4. **Verification Record & Status Tracking Module** — append-only audit trail
5. **OCR Module** — extracts text from uploaded images (Tesseract) and PDFs
6. **Admin Dashboard** — counts, status breakdown, recent activity
7. **Property Location Map** — geocoding + Leaflet map + Google Maps/Directions

**Phase 2 (100%)**
8. **NLP Cross-Document Field Matching** — extracts owner names, survey
   numbers, areas, dates, PIN codes from OCR text and compares them across
   a property's documents
9. **ML/Rule-Based Fraud & Anomaly Detection** — a weighted, explainable
   scoring engine (drop-in replaceable by a trained classifier later)
10. **Risk Scoring** — transparent 0–100 score with Low/Medium/High level
    and a plain-language reason for every point added
11. **Verification Report Generation** — downloadable PDF per property
12. **Human Review / Override Workflow** — an admin Review Queue, riskiest
    properties first; AI only ever moves a property to "In Review," never
    to Verified/Rejected
13. **Advanced Analytics Dashboard** — OCR success rate, risk distribution,
    analyses run, alongside the original counts

Plus, on request: a **property photo slideshow** and a full **UI refresh**
(new teal/gold color system, light navbar, refreshed hero, stamp-seal login
animation).

---

## 1. Requirements

- Python 3.10+
- **Tesseract OCR** installed on your system (needed only for documents you
  upload yourself — the seeded demo data comes with OCR text pre-filled, so
  you can explore NLP/risk scoring without installing Tesseract first):
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- A database: SQLite works with zero setup; MySQL/PostgreSQL supported via
  `DATABASE_URL`.

## 2. Setup

```bash
cd property_verification
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configuration (optional)

```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost/property_verification"
# or: export DATABASE_URL="postgresql+psycopg2://username:password@localhost/property_verification"
export TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"   # Windows only, if needed
export SECRET_KEY="something-long-and-random"
```

## 4. Run

```bash
python app.py
```

Visit **http://127.0.0.1:5000**. The **first account you register becomes
admin**; every account after that is a normal property-owner user.

## 5. See it fully working right away (recommended)

Rather than manually creating properties/documents to see the AI features,
run the seed script once the app's tables exist (first run of `python
app.py` creates them):

```bash
python scripts/seed_demo.py
```

This creates:
- an **admin** login: `admin@propverify.com` / `Admin@123`
- an **owner** login: `owner@propverify.com` / `Owner@123`
- **3 properties** with realistic pre-filled OCR text, already analyzed:
  one clean (Low risk), one with a minor mismatch (Medium risk), and one
  with several deliberate inconsistencies (High risk) — so the Review Queue
  and PDF report have something real to show.
- **5 generated demo photos** on the first property (a slideshow), plus one
  photo each on the other two.

Safe to re-run; it skips anything already created.

## 6. If you already have an existing database with real data

`db.create_all()` (used automatically on every app start) only creates
tables that don't exist yet — it never alters a table you already have. New
tables from this build (`analysis_results`, `property_photos`) are created
automatically either way. But the **location columns added to the existing
`properties` table** (locality, city, state, pincode, latitude, longitude)
need one manual step on a pre-existing database:

```bash
python scripts/migrate_add_location_fields.py
```

It only **adds** columns — it never touches or deletes existing rows.

## 7. How the AI pipeline fits together

```
Document upload → OCR (routes/ocr.py) → extracted_text stored
        ↓
"Run Automated Verification" button on a property
        ↓
analysis/extractor.py   — pulls structured fields out of each document's text
analysis/matcher.py     — fuzzy name matching, survey/area comparison helpers
analysis/risk.py        — runs ~9 checks, produces score + explainable findings
        ↓
AnalysisResult stored → property moves Pending → In Review (never further —
that decision is left to a human)
        ↓
Admin opens Review Queue (riskiest first) → opens the property → reads the
findings → downloads the PDF report (analysis/report.py) → sets the final
status (Verified/Rejected) via the existing Verification module
```

The risk engine (`analysis/risk.py`) is intentionally rule-based and fully
explainable rather than a black-box model, per the project's scope of
*technical support, not legal certification*. `compute_risk()`'s `features`
output is already a numeric vector, so swapping in a trained classifier
(e.g. scikit-learn) later is a matter of replacing the scoring function, not
re-architecting anything upstream.

## 8. Property Location Map feature

- Add/Edit Property captures Area/Locality, City, State, PIN Code.
- Address is geocoded via **OpenStreetMap Nominatim** (free, no API key).
- Property detail page shows an embedded Leaflet map, "Open in Google Maps,"
  and "Get Directions," all falling back gracefully to an address-based
  link if geocoding didn't find coordinates.

## 9. Property photo slideshow

- Property detail page has an upload box (multiple files at once) and shows
  a Bootstrap carousel when photos exist.
- Demo photos are **procedurally generated illustrations** (via
  `scripts/generate_demo_photos.py`, using only PIL primitives) rather than
  downloaded stock photos, so there's no licensing concern with the seeded
  data. Real property photos uploaded by users work the same way.

## 10. Testing

A pytest suite covers the NLP extractor, the matcher helpers, and the risk
engine -- including a parametrized test that runs the real engine against
all 13 scenarios in `scripts/demo_data.py` and checks each lands on its
documented expected risk level (Low/Medium/High).

```bash
pip install -r requirements-dev.txt
pytest
```

The same known-answer scenarios are also viewable live in the app: log in
as an admin and open **Admin Dashboard → Model Evaluation** to see the
engine's accuracy against them, with a breakdown per risk level and the
top findings behind each result. This is a reproducible stand-in for a
labeled fraud dataset (which doesn't exist for this project) -- it checks
the engine behaves as designed, not that it generalizes to real-world
documents it's never seen.

## 11. Known limitations / good next steps

- OCR, and now the analysis run, execute synchronously on the request
  thread — fine at this scale; move to a task queue (Celery/RQ) if document
  volume grows.
- Scanned/image-only PDFs return empty OCR text (no embedded text layer to
  extract); page-rasterization + Tesseract would close this gap.
- The NLP extractor is regex/pattern-based, tuned to the document phrasing
  used in the seed data and typical Indian property documents (Owner:,
  Survey No:, sq ft, etc.) — real-world documents with very different
  phrasing may need extra patterns added to `analysis/extractor.py`.
- The risk engine's point weights are a reasonable starting rubric, not
  a calibrated model — once real verified/rejected outcomes accumulate,
  those labels are exactly what's needed to train a proper classifier
  using the existing `features` vector.
