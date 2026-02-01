from models.database import db
from models.document import Document
from models.transaction import Transaction
from models.category import Category
from models.budget import Budget
from datetime import datetime, timedelta
from sqlalchemy import func, extract

class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def get_dashboard_stats():
        """Get statistics for dashboard"""
        total_docs = Document.query.count()
        total_transactions = Transaction.query.count()
        total_categories = Category.query.count()
        
        # Calculate total expenses
        total_expenses = db.session.query(func.sum(Transaction.amount)).scalar() or 0.0
        
        # Get current month expenses
        today = datetime.now()
        current_month_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            extract('month', Transaction.transaction_date) == today.month,
            extract('year', Transaction.transaction_date) == today.year
        ).scalar() or 0.0
        
        # Get last month expenses
        last_month = today.replace(day=1) - timedelta(days=1)
        last_month_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            extract('month', Transaction.transaction_date) == last_month.month,
            extract('year', Transaction.transaction_date) == last_month.year
        ).scalar() or 0.0
        
        # Calculate percentage change
        if last_month_expenses > 0:
            change_percentage = ((current_month_expenses - last_month_expenses) / last_month_expenses) * 100
        else:
            change_percentage = 0.0
        
        return {
            'total_documents': total_docs,
            'total_transactions': total_transactions,
            'total_categories': total_categories,
            'total_expenses': round(total_expenses, 2),
            'current_month_expenses': round(current_month_expenses, 2),
            'last_month_expenses': round(last_month_expenses, 2),
            'change_percentage': round(change_percentage, 2)
        }
    
    @staticmethod
    def get_category_breakdown():
        """Get category-wise expense breakdown"""
        categories = Category.query.all()
        breakdown = []
        
        for category in categories:
            total = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.category_id == category.id
            ).scalar() or 0.0
            
            if total > 0:
                breakdown.append({
                    'id': category.id,
                    'name': category.name,
                    'icon': category.icon,
                    'color': category.color,
                    'total': round(total, 2),
                    'transaction_count': Transaction.query.filter_by(category_id=category.id).count()
                })
        
        # Sort by total descending
        breakdown.sort(key=lambda x: x['total'], reverse=True)
        return breakdown
    
    @staticmethod
    def get_recent_transactions(limit=10):
        """Get recent transactions"""
        transactions = Transaction.query.order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc()
        ).limit(limit).all()
        
        return [t.to_dict() for t in transactions]
    
    @staticmethod
    def get_monthly_trend(months=6):
        """Get monthly spending trend"""
        today = datetime.now()
        trends = []
        
        for i in range(months):
            month_date = today - timedelta(days=30*i)
            month_total = db.session.query(func.sum(Transaction.amount)).filter(
                extract('month', Transaction.transaction_date) == month_date.month,
                extract('year', Transaction.transaction_date) == month_date.year
            ).scalar() or 0.0
            
            trends.append({
                'month': month_date.strftime('%B'),
                'year': month_date.year,
                'total': round(month_total, 2)
            })
        
        trends.reverse()
        return trends
    
    @staticmethod
    def get_top_vendors(limit=5):
        """Get top vendors by spending"""
        vendors = db.session.query(
            Transaction.vendor_name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.vendor_name.isnot(None)
        ).group_by(Transaction.vendor_name).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(limit).all()
        
        return [
            {
                'vendor': v.vendor_name,
                'total': round(v.total, 2),
                'transaction_count': v.count
            }
            for v in vendors
        ]