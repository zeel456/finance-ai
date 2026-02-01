"""
Conversation Model
Save as: models/conversation.py
"""

from models.database import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }
    
    def to_dict_detailed(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages]
        }
    
    @staticmethod
    def generate_title(first_message):
        """Generate a title from the first message"""
        if len(first_message) > 50:
            return first_message[:50] + '...'
        return first_message