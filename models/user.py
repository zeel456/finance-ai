"""
User Model for Authentication
Finance AI Assistant - Multi-User Support
"""

from models.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication and multi-user support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    full_name = db.Column(db.String(120))
    profile_picture = db.Column(db.String(255))  # URL or path
    
    # Account settings
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', 
                                  foreign_keys='Transaction.user_id')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic',
                            foreign_keys='Budget.user_id')
    documents = db.relationship('Document', backref='user', lazy='dynamic',
                              foreign_keys='Document.user_id')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # Password methods
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login required methods
    def get_id(self):
        """Return user ID as string"""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """Return True if user is authenticated"""
        return True
    
    @property
    def is_anonymous(self):
        """Return False - users are not anonymous"""
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # API methods
    def to_dict(self):
        """Convert to dictionary for API responses"""
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
        """Public profile info (no sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'profile_picture': self.profile_picture
        }
    
    # Statistics
    def get_transaction_count(self):
        """Get total transaction count for user"""
        return self.transactions.count()
    
    def get_total_expenses(self):
        """Get total expenses for user"""
        from sqlalchemy import func
        result = db.session.query(
            func.sum(db.text('transactions.amount'))
        ).filter(
            db.text('transactions.user_id = :user_id')
        ).params(user_id=self.id).scalar()
        return float(result) if result else 0.0
    
    def get_budget_count(self):
        """Get budget count for user"""
        return self.budgets.count()
    
    def get_document_count(self):
        """Get document count for user"""
        return self.documents.count()
    
    @classmethod
    def create_user(cls, username, email, password, full_name=None):
        """
        Create new user with validation
        
        Returns:
            (User object, error message) - error is None if successful
        """
        # Validate username
        if len(username) < 3:
            return None, "Username must be at least 3 characters"
        
        if cls.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        # Validate email
        if '@' not in email:
            return None, "Invalid email address"
        
        if cls.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        # Validate password
        if len(password) < 6:
            return None, "Password must be at least 6 characters"
        
        # Create user
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
            return None, f"Error creating user: {str(e)}"
    
    @classmethod
    def authenticate(cls, username_or_email, password):
        """
        Authenticate user with username/email and password
        
        Returns:
            User object if successful, None otherwise
        """
        # Try to find by username or email
        user = cls.query.filter(
            (cls.username == username_or_email) | 
            (cls.email == username_or_email)
        ).first()
        
        if user and user.is_active and user.check_password(password):
            user.update_last_login()
            return user
        
        return None
    
    def deactivate(self):
        """Deactivate user account"""
        self.is_active = False
        db.session.commit()
    
    def activate(self):
        """Activate user account"""
        self.is_active = True
        db.session.commit()