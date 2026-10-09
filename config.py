import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Central configuration.

    DATABASE_URL examples (set as an environment variable before running):
      MySQL:      mysql+pymysql://user:password@localhost/property_verification
      PostgreSQL: postgresql+psycopg2://user:password@localhost/property_verification
      SQLite (default, zero-setup, good for development/demo):
                  sqlite:///property_verification.db
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'property_verification.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

    # Path to the tesseract binary. On Windows this typically needs to be set
    # explicitly, e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")

    # Email notifications (optional). If MAIL_SERVER isn't set, the app
    # never attempts to send mail -- status-change notifications are simply
    # logged instead, so email is entirely opt-in and the app works with
    # zero mail configuration. To enable, set these as environment
    # variables (e.g. for Gmail: smtp.gmail.com, port 587, TLS on, and an
    # app password -- never your real account password):
    #   export MAIL_SERVER=smtp.gmail.com
    #   export MAIL_PORT=587
    #   export MAIL_USE_TLS=true
    #   export MAIL_USERNAME=you@example.com
    #   export MAIL_PASSWORD=your-app-password
    #   export MAIL_DEFAULT_SENDER=you@example.com
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    MAIL_ENABLED = bool(MAIL_SERVER)
