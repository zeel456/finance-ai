"""
Message Model
Save as: models/message.py
"""

from models.database import db
from datetime import datetime
import json

class Message(db.Model):
    __tablename__ = 'messages'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    
    # AI metadata
    intent = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    entities = db.Column(db.Text)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'intent': self.intent,
            'confidence': self.confidence,
            'entities': json.loads(self.entities) if self.entities else None,
            'created_at': self.created_at.isoformat()
        }
    
    def set_entities(self, entities_dict):
        """Convert entities dict to JSON string"""
        self.entities = json.dumps(entities_dict)
    
    def get_entities(self):
        """Get entities as dict"""
        return json.loads(self.entities) if self.entities else {}