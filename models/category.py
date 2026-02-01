from models.database import db

class Category(db.Model):
    """Expense categories"""
    __tablename__ = 'categories'


    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))
    monthly_budget = db.Column(db.Float, default=0.0)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def get_total_spent(self, month=None, year=None):
        """Calculate total spent in this category"""
        from models.transaction import Transaction
        from datetime import datetime
        
        query = Transaction.query.filter_by(category_id=self.id)
        
        if month and year:
            query = query.filter(
                db.extract('month', Transaction.transaction_date) == month,
                db.extract('year', Transaction.transaction_date) == year
            )
        
        total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.category_id == self.id
        )
        
        if month and year:
            total = total.filter(
                db.extract('month', Transaction.transaction_date) == month,
                db.extract('year', Transaction.transaction_date) == year
            )
        
        result = total.scalar()
        return result if result else 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'monthly_budget': self.monthly_budget,
            'total_spent': self.get_total_spent()
        }

# Default categories to seed
DEFAULT_CATEGORIES = [
    {'name': 'Food & Dining', 'icon': '🍔', 'color': '#FF6B6B', 'description': 'Restaurants, groceries, food delivery'},
    {'name': 'Transportation', 'icon': '🚗', 'color': '#4ECDC4', 'description': 'Fuel, public transport, ride-sharing'},
    {'name': 'Shopping', 'icon': '🛍️', 'color': '#45B7D1', 'description': 'Clothing, electronics, online shopping'},
    {'name': 'Entertainment', 'icon': '🎬', 'color': '#96CEB4', 'description': 'Movies, games, subscriptions'},
    {'name': 'Utilities', 'icon': '💡', 'color': '#FFEAA7', 'description': 'Electricity, water, internet, phone'},
    {'name': 'Healthcare', 'icon': '🏥', 'color': '#DFE6E9', 'description': 'Medical expenses, pharmacy, insurance'},
    {'name': 'Education', 'icon': '📚', 'color': '#74B9FF', 'description': 'Courses, books, tuition'},
    {'name': 'Travel', 'icon': '✈️', 'color': '#A29BFE', 'description': 'Flights, hotels, vacation'},
    {'name': 'Insurance', 'icon': '🛡️', 'color': '#FD79A8', 'description': 'Life, health, vehicle insurance'},
    {'name': 'Other', 'icon': '📌', 'color': '#636E72', 'description': 'Miscellaneous expenses'}
]