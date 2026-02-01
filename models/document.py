from models.database import db
from datetime import datetime

class Document(db.Model):
    """Uploaded document model"""
    __tablename__ = 'documents'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # invoice, receipt, statement
    file_path = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    raw_text = db.Column(db.Text)
    
    # Relationship to transactions
    transactions = db.relationship('Transaction', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'upload_date': self.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'processed': self.processed
        }