"""
Comprehensive Notification System for Finance AI
Handles alerts, notifications, and real-time updates
"""

from models.database import db
from datetime import datetime
from sqlalchemy import desc
import json

class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notifications'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification details
    type = db.Column(db.String(50), nullable=False)  # budget_alert, transaction_added, etc.
    severity = db.Column(db.String(20), nullable=False)  # info, warning, danger, success
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related entities
    related_type = db.Column(db.String(50))  # budget, transaction, document
    related_id = db.Column(db.Integer)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    
    # Actions (JSON)
    action_url = db.Column(db.String(500))
    action_label = db.Column(db.String(100))
    
    # Extra data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = db.Column(db.Text)  # JSON string for extra data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'extra_data': json.loads(self.extra_data) if self.extra_data else None,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'time_ago': self._get_time_ago()
        }
    
    def _get_time_ago(self):
        """Get human-readable time difference"""
        delta = datetime.utcnow() - self.created_at
        
        if delta.days > 7:
            return self.created_at.strftime('%b %d, %Y')
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "Just now"


class NotificationManager:
    """Manages all notification operations"""
    
    @staticmethod
    def create_notification(type, severity, title, message, 
                          related_type=None, related_id=None,
                          action_url=None, action_label=None,
                          extra_data=None, user_id=None):
        """Create a new notification"""
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                severity=severity,
                title=title,
                message=message,
                related_type=related_type,
                related_id=related_id,
                action_url=action_url,
                action_label=action_label,
                extra_data=json.dumps(extra_data) if extra_data else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
            print(f"✅ Notification created: {title}")
            return notification
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating notification: {e}")
            return None
    
    @staticmethod
    def get_notifications(user_id=None, unread_only=False, limit=50):
        """Get notifications"""
        query = Notification.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False, is_dismissed=False)
        
        query = query.filter_by(is_dismissed=False)
        query = query.order_by(desc(Notification.created_at))
        query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark notification as read"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id=None):
        """Mark all notifications as read"""
        query = Notification.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        count = query.update({'is_read': True, 'read_at': datetime.utcnow()})
        db.session.commit()
        
        return count
    
    @staticmethod
    def dismiss_notification(notification_id):
        """Dismiss notification"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_dismissed = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_unread_count(user_id=None):
        """Get count of unread notifications"""
        query = Notification.query.filter_by(is_read=False, is_dismissed=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.count()
    
    @staticmethod
    def delete_old_notifications(days=30):
        """Delete notifications older than specified days"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        count = Notification.query.filter(
            Notification.created_at < cutoff
        ).delete()
        
        db.session.commit()
        return count


class BudgetNotificationManager:
    """Specialized manager for budget-related notifications"""
    
    @staticmethod
    def check_and_notify_budget_status(budget):
        """Check budget status and create appropriate notifications"""
        percentage = budget.percentage_used
        
        # 100%+ Over budget
        if percentage >= 100:
            NotificationManager.create_notification(
                type='budget_exceeded',
                severity='danger',
                title=f'🚨 Budget Exceeded: {budget.category.name}',
                message=f'You have exceeded your {budget.category.name} budget by ₹{abs(budget.remaining):,.2f}. Consider reviewing your spending.',
                related_type='budget',
                related_id=budget.id,
                action_url=f'/budgets?highlight={budget.id}',
                action_label='View Budget',
                extra_data={
                    'category': budget.category.name,
                    'budget_amount': budget.amount,
                    'spent': budget.spent,
                    'percentage': percentage
                }
            )
        
        # 90-99% Warning
        elif percentage >= 90:
            NotificationManager.create_notification(
                type='budget_warning',
                severity='warning',
                title=f'⚠️ Budget Alert: {budget.category.name}',
                message=f'You have used {percentage}% of your {budget.category.name} budget. Only ₹{budget.remaining:,.2f} remaining.',
                related_type='budget',
                related_id=budget.id,
                action_url=f'/budgets?highlight={budget.id}',
                action_label='View Budget',
                extra_data={
                    'category': budget.category.name,
                    'budget_amount': budget.amount,
                    'spent': budget.spent,
                    'percentage': percentage
                }
            )
        
        # 75-89% Info
        elif percentage >= 75:
            NotificationManager.create_notification(
                type='budget_approaching',
                severity='info',
                title=f'ℹ️ Budget Update: {budget.category.name}',
                message=f'You have used {percentage}% of your {budget.category.name} budget.',
                related_type='budget',
                related_id=budget.id,
                action_url=f'/budgets?highlight={budget.id}',
                action_label='View Budget',
                extra_data={
                    'category': budget.category.name,
                    'budget_amount': budget.amount,
                    'spent': budget.spent,
                    'percentage': percentage
                }
            )
    
    @staticmethod
    def notify_transaction_added(transaction):
        """Notify when a transaction is added"""
        NotificationManager.create_notification(
            type='transaction_added',
            severity='success',
            title='✅ Transaction Added',
            message=f'₹{transaction.amount:,.2f} spent at {transaction.vendor_name}',
            related_type='transaction',
            related_id=transaction.id,
            action_url=f'/transactions?highlight={transaction.id}',
            action_label='View Transaction',
            extra_data={
                'amount': transaction.amount,
                'vendor': transaction.vendor_name,
                'category': transaction.category.name if transaction.category else 'Uncategorized'
            }
        )
    
    @staticmethod
    def notify_document_processed(document, transaction_count):
        """Notify when a document is processed"""
        NotificationManager.create_notification(
            type='document_processed',
            severity='success',
            title='📄 Document Processed',
            message=f'{document.original_filename} processed successfully. {transaction_count} transaction(s) extracted.',
            related_type='document',
            related_id=document.id,
            action_url=f'/upload?doc={document.id}',
            action_label='View Details',
            extra_data={
                'filename': document.original_filename,
                'transaction_count': transaction_count
            }
        )
    
    @staticmethod
    def notify_monthly_summary(month, year, total_spent, budget_exceeded_count):
        """Notify with monthly summary"""
        NotificationManager.create_notification(
            type='monthly_summary',
            severity='info',
            title=f'📊 Monthly Summary - {month}/{year}',
            message=f'Total spent: ₹{total_spent:,.2f}. {budget_exceeded_count} budget(s) exceeded.',
            action_url='/insights',
            action_label='View Insights',
            extra_data={
                'month': month,
                'year': year,
                'total_spent': total_spent,
                'budget_exceeded_count': budget_exceeded_count
            }
        )