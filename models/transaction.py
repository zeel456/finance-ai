"""
Updated Transaction Model with HDFC Email Sync Support
Replace your existing models/transaction.py with this
"""

from models.database import db
from datetime import datetime

class Transaction(db.Model):
    """Extracted transaction model with bank sync support"""
    __tablename__ = 'transactions'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    
    # Extracted data
    transaction_date = db.Column(db.Date)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    vendor_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    
    # Categorization
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    payment_method = db.Column(db.String(50))  # cash, card, upi, etc.
    
    # Tax information
    tax_amount = db.Column(db.Float, default=0.0)
    tax_percentage = db.Column(db.Float)
    
    # ============================================================================
    # NEW FIELDS FOR BANK SYNC
    # ============================================================================
    
    # Source tracking
    source = db.Column(db.String(50), default='manual', index=True)
    # Values: 'manual', 'hdfc_email', 'hdfc_statement', 'upload', 'api'
    
    # Deduplication hash (prevents duplicate imports)
    transaction_hash = db.Column(db.String(32), unique=True, nullable=True, index=True)
    # MD5 hash of: amount + vendor + date + reference
    
    # Bank transaction details
    reference_number = db.Column(db.String(100), nullable=True)
    # UPI reference, transaction ID, check number, etc.
    
    account_number = db.Column(db.String(20), nullable=True)
    # Last 4 digits of account (e.g., "XX1234")
    
    # Transaction type (for income vs expense)
    transaction_type = db.Column(db.String(20), default='debit')
    # Values: 'debit' (expense), 'credit' (income)
    
    # ============================================================================
    # METADATA
    # ============================================================================
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete flag (optional - for keeping history)
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Transaction {self.vendor_name} - ₹{self.amount} [{self.source}]>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'date': self.transaction_date.strftime('%Y-%m-%d') if self.transaction_date else None,
            'amount': self.amount,
            'currency': self.currency,
            'vendor': self.vendor_name,
            'description': self.description,
            'category': self.category.name if self.category else 'Uncategorized',
            'category_id': self.category_id,
            'payment_method': self.payment_method,
            'tax_amount': self.tax_amount,
            'tax_percentage': self.tax_percentage,
            
            # New fields
            'source': self.source,
            'reference_number': self.reference_number,
            'account_number': self.account_number,
            'transaction_type': self.transaction_type,
            'transaction_hash': self.transaction_hash,
            
            # Timestamps
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_detailed(self):
        """Detailed dictionary with relationships"""
        base = self.to_dict()
        
        # Add document info if exists
        if self.document:
            base['document'] = {
                'id': self.document.id,
                'filename': self.document.original_filename,
                'file_type': self.document.file_type
            }
        
        # Add category details
        if self.category:
            base['category_details'] = {
                'id': self.category.id,
                'name': self.category.name,
                'icon': self.category.icon,
                'color': self.category.color
            }
        
        return base
    
    @staticmethod
    def generate_hash(amount, vendor_name, transaction_date, reference_number=None):
        """
        Generate unique hash for deduplication
        
        Args:
            amount: Transaction amount
            vendor_name: Vendor/merchant name
            transaction_date: Date of transaction (datetime.date object or string)
            reference_number: Optional reference/UPI ID
            
        Returns:
            32-character MD5 hash
        """
        import hashlib
        
        # Convert date to string if needed
        if isinstance(transaction_date, datetime):
            date_str = transaction_date.strftime('%Y-%m-%d')
        else:
            date_str = str(transaction_date)
        
        # Create hash string
        hash_string = f"{amount}_{vendor_name}_{date_str}_{reference_number or ''}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    @classmethod
    def find_duplicate(cls, amount, vendor_name, transaction_date, reference_number=None):
        """
        Check if transaction already exists (deduplication)
        
        Returns:
            Transaction object if duplicate found, None otherwise
        """
        # Method 1: Check by hash (fastest)
        if reference_number or vendor_name:
            trans_hash = cls.generate_hash(amount, vendor_name, transaction_date, reference_number)
            existing = cls.query.filter_by(transaction_hash=trans_hash).first()
            if existing:
                return existing
        
        # Method 2: Check by fields (fallback)
        existing = cls.query.filter_by(
            amount=amount,
            vendor_name=vendor_name,
            transaction_date=transaction_date
        ).first()
        
        return existing
    
    @classmethod
    def get_by_source(cls, source, limit=100):
        """Get transactions by source"""
        return cls.query.filter_by(source=source).order_by(
            cls.transaction_date.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_hdfc_synced_count(cls):
        """Get count of HDFC synced transactions"""
        return cls.query.filter_by(source='hdfc_email').count()
    
    @classmethod
    def get_total_by_source(cls):
        """Get transaction count grouped by source"""
        from sqlalchemy import func
        
        results = db.session.query(
            cls.source,
            func.count(cls.id).label('count'),
            func.sum(cls.amount).label('total_amount')
        ).group_by(cls.source).all()
        
        return [
            {
                'source': r.source,
                'count': r.count,
                'total_amount': float(r.total_amount) if r.total_amount else 0
            }
            for r in results
        ]
    
    def mark_as_income(self):
        """Mark transaction as income (credit)"""
        self.transaction_type = 'credit'
    
    def mark_as_expense(self):
        """Mark transaction as expense (debit)"""
        self.transaction_type = 'debit'
    
    def is_income(self):
        """Check if transaction is income"""
        return self.transaction_type == 'credit'
    
    def is_expense(self):
        """Check if transaction is expense"""
        return self.transaction_type == 'debit'
    
    def soft_delete(self):
        """Soft delete transaction (keep in database but mark as deleted)"""
        self.is_deleted = True
        db.session.commit()
    
    def restore(self):
        """Restore soft-deleted transaction"""
        self.is_deleted = False
        db.session.commit()


# ============================================================================
# DATABASE MIGRATION HELPER
# ============================================================================

def upgrade_transaction_table():
    """
    Helper function to upgrade existing transaction table
    Run this once after updating the model
    """
    from models.database import db
    
    print("🔄 Upgrading transaction table...")
    
    try:
        # Create new columns if they don't exist
        with db.engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(db.text(
                "PRAGMA table_info(transactions)"
            ))
            existing_columns = [row[1] for row in result]
            
            # Add missing columns
            new_columns = {
                'source': "ALTER TABLE transactions ADD COLUMN source VARCHAR(50) DEFAULT 'manual'",
                'transaction_hash': "ALTER TABLE transactions ADD COLUMN transaction_hash VARCHAR(32) UNIQUE",
                'reference_number': "ALTER TABLE transactions ADD COLUMN reference_number VARCHAR(100)",
                'account_number': "ALTER TABLE transactions ADD COLUMN account_number VARCHAR(20)",
                'transaction_type': "ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'debit'",
                'is_deleted': "ALTER TABLE transactions ADD COLUMN is_deleted BOOLEAN DEFAULT 0"
            }
            
            for col_name, sql in new_columns.items():
                if col_name not in existing_columns:
                    conn.execute(db.text(sql))
                    conn.commit()
                    print(f"   ✅ Added column: {col_name}")
                else:
                    print(f"   ⏭️  Column exists: {col_name}")
        
        print("✅ Transaction table upgraded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Upgrade failed: {e}")
        return False


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# Create manual transaction
transaction = Transaction(
    amount=1250.00,
    vendor_name="Swiggy",
    transaction_date=datetime.now().date(),
    category_id=1,
    source='manual'
)

# Create HDFC synced transaction
transaction = Transaction(
    amount=2500.00,
    vendor_name="Amazon",
    transaction_date=datetime.now().date(),
    category_id=2,
    source='hdfc_email',
    reference_number='UPI12345678',
    account_number='XX1234',
    transaction_hash=Transaction.generate_hash(2500, 'Amazon', datetime.now().date(), 'UPI12345678')
)

# Check for duplicates before saving
existing = Transaction.find_duplicate(
    amount=1250,
    vendor_name="Swiggy",
    transaction_date=datetime.now().date()
)

if not existing:
    db.session.add(transaction)
    db.session.commit()
else:
    print("Transaction already exists!")

# Get all HDFC synced transactions
hdfc_transactions = Transaction.get_by_source('hdfc_email')

# Get source statistics
stats = Transaction.get_total_by_source()
# Returns: [{'source': 'manual', 'count': 150, 'total_amount': 45000}, ...]
"""