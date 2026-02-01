from models.database import db
from datetime import datetime

class Budget(db.Model):
    """Monthly budget tracking"""
    __tablename__ = 'budgets'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    spent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for category + month + year
    __table_args__ = (
        db.UniqueConstraint('category_id', 'month', 'year', name='unique_budget_period'),
    )
    
    def __repr__(self):
        return f'<Budget {self.category.name} {self.month}/{self.year}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'month': self.month,
            'year': self.year,
            'amount': self.amount,
            'spent': self.spent,
            'remaining': self.amount - self.spent,
            'percentage_used': round((self.spent / self.amount * 100), 2) if self.amount > 0 else 0
        }