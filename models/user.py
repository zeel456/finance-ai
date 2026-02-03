"""
User Model for Authentication - PRODUCTION SAFE
Save as: models/user.py

✅ Flask-Login compliant
✅ No 500 errors
✅ Railway / Gunicorn safe
"""

from models.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func


class User(UserMixin, db.Model):
    """User model for authentication and multi-user support"""

    __tablename__ = 'users'

    # ======================================================================
    # CORE FIELDS
    # ======================================================================
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    full_name = db.Column(db.String(120))
    profile_picture = db.Column(db.String(255))

    # Account flags
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login = db.Column(db.DateTime)

    # ======================================================================
    # RELATIONSHIPS
    # ======================================================================
    transactions = db.relationship(
        'Transaction',
        backref='user',
        lazy='dynamic',
        foreign_keys='Transaction.user_id'
    )

    budgets = db.relationship(
        'Budget',
        backref='user',
        lazy='dynamic',
        foreign_keys='Budget.user_id'
    )

    documents = db.relationship(
        'Document',
        backref='user',
        lazy='dynamic',
        foreign_keys='Document.user_id'
    )

    # ======================================================================
    # FLASK-LOGIN (DO NOT OVERRIDE CORE PROPERTIES)
    # ======================================================================
    def get_id(self):
        """Return user ID as string (Flask-Login requirement)"""
        return str(self.id)

    # ⚠️ DO NOT define:
    # - is_authenticated
    # - is_anonymous
    # - is_active
    # UserMixin already provides them correctly

    # ======================================================================
    # PASSWORD METHODS
    # ======================================================================
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ======================================================================
    # AUTH HELPERS
    # ======================================================================
    def update_last_login(self):
        """Update last login timestamp (caller commits)"""
        self.last_login = datetime.utcnow()

    @classmethod
    def authenticate(cls, username_or_email: str, password: str):
        """
        Authenticate user by username OR email

        Returns:
            User | None
        """
        user = cls.query.filter(
            (cls.username == username_or_email) |
            (cls.email == username_or_email)
        ).first()

        if not user:
            print(f"❌ User not found: {username_or_email}", flush=True)
            return None

        if not user.is_active:
            print(f"❌ User inactive: {username_or_email}", flush=True)
            return None

        if not user.check_password(password):
            print(f"❌ Invalid password for: {username_or_email}", flush=True)
            return None

        user.update_last_login()
        print(f"✅ Login successful: {user.username}", flush=True)
        return user

    @classmethod
    def create_user(cls, username, email, password, full_name=None):
        """Create a new user safely"""

        if len(username) < 3:
            return None, "Username must be at least 3 characters"

        if cls.query.filter_by(username=username).first():
            return None, "Username already exists"

        if '@' not in email:
            return None, "Invalid email address"

        if cls.query.filter_by(email=email).first():
            return None, "Email already registered"

        if len(password) < 6:
            return None, "Password must be at least 6 characters"

        user = cls(
            username=username,
            email=email,
            full_name=full_name or username
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    # ======================================================================
    # STATS / API
    # ======================================================================
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'profile_picture': self.profile_picture,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def to_dict_public(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'profile_picture': self.profile_picture
        }

    def get_transaction_count(self):
        return self.transactions.count()

    def get_total_expenses(self):
        total = db.session.query(
            func.sum(func.coalesce(db.text("transactions.amount"), 0))
        ).filter(
            db.text("transactions.user_id = :uid")
        ).params(uid=self.id).scalar()

        return float(total or 0)

    def get_budget_count(self):
        return self.budgets.count()

    def get_document_count(self):
        return self.documents.count()

    # ======================================================================
    # ADMIN ACTIONS
    # ======================================================================
    def deactivate(self):
        self.is_active = False
        db.session.commit()

    def activate(self):
        self.is_active = True
        db.session.commit()

    def __repr__(self):
        return f"<User {self.username}>"
