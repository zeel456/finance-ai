"""
Notification Routes Blueprint
Complete API endpoints for notification management
Location: routes/notification_routes.py
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.notification_system import (
    NotificationManager, 
    BudgetNotificationManager,
    Notification
)
from models.database import db
from datetime import datetime

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notification_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """
    Get all notifications with optional filtering
    Query params:
        - unread_only: boolean (default: false)
        - limit: int (default: 50)
        - type: string (filter by notification type)
    """
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        notification_type = request.args.get('type')
        
        notifications = NotificationManager.get_notifications(
            unread_only=unread_only,
            limit=limit,
            user_id=current_user.id
        )
        
        # Additional type filtering if specified
        if notification_type:
            notifications = [n for n in notifications if notification_type in n.type]
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications)
        })
        
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    try:
        count = NotificationManager.get_unread_count(current_user.id)
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error getting unread count: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/<int:notification_id>', methods=['GET'])
@login_required
def get_single_notification(notification_id):
    """Get a single notification by ID"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
        return jsonify({
            'success': True,
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        print(f"❌ Error getting notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        success = NotificationManager.mark_as_read(notification_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    try:
        count = NotificationManager.mark_all_as_read(user_id=current_user.id)
        
        return jsonify({
            'success': True,
            'message': f'{count} notification(s) marked as read',
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error marking all as read: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/<int:notification_id>/dismiss', methods=['POST'])
@login_required
def dismiss_notification(notification_id):
    """Dismiss/hide a notification"""
    try:
        success = NotificationManager.dismiss_notification(notification_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification dismissed'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error dismissing notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/dismiss-all', methods=['POST'])
@login_required
def dismiss_all_notifications():
    """Dismiss all notifications"""
    try:
        query = Notification.query.filter_by(user_id=current_user.id)
        
        count = query.update({'is_dismissed': True})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} notification(s) dismissed',
            'count': count
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error dismissing all notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/stats', methods=['GET'])
@login_required
def get_notification_stats():
    """Get notification statistics"""
    try:
        total = Notification.query.filter_by(user_id=current_user.id).count()
        unread = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False,
            is_dismissed=False
        ).count()
        dismissed = Notification.query.filter_by(
            user_id=current_user.id,
            is_dismissed=True
        ).count()
        
        # Count by type
        from sqlalchemy import func
        by_type = db.session.query(
            Notification.type,
            func.count(Notification.id)
        ).filter_by(
            user_id=current_user.id
        ).group_by(Notification.type).all()
        
        # Count by severity
        by_severity = db.session.query(
            Notification.severity,
            func.count(Notification.id)
        ).filter_by(
            user_id=current_user.id
        ).group_by(Notification.severity).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'unread': unread,
                'dismissed': dismissed,
                'by_type': {t: c for t, c in by_type},
                'by_severity': {s: c for s, c in by_severity}
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting notification stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """
    Create a test notification (for development/testing)
    Request body (all optional):
        - type: string
        - severity: string (info, warning, danger, success)
        - title: string
        - message: string
        - action_url: string
        - action_label: string
    """
    try:
        data = request.get_json() or {}
        
        notification = NotificationManager.create_notification(
            type=data.get('type', 'test'),
            severity=data.get('severity', 'info'),
            title=data.get('title', 'Test Notification'),
            message=data.get('message', 'This is a test notification'),
            action_url=data.get('action_url'),
            action_label=data.get('action_label'),
            extra_data=data.get('extra_data'),
            user_id=current_user.id
        )
        
        if notification:
            return jsonify({
                'success': True,
                'message': 'Test notification created',
                'notification': notification.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create notification'
            }), 500
            
    except Exception as e:
        print(f"❌ Error creating test notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_old_notifications():
    """
    Delete old notifications (admin/maintenance endpoint)
    Query params:
        - days: int (default: 30) - Delete notifications older than this
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 7:
            return jsonify({
                'success': False,
                'error': 'Minimum cleanup period is 7 days'
            }), 400
        
        count = NotificationManager.delete_old_notifications(days, current_user.id)
        
        return jsonify({
            'success': True,
            'message': f'{count} old notification(s) deleted',
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error cleaning up notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_notification_action():
    """
    Perform bulk actions on notifications
    Request body:
        - notification_ids: list of int
        - action: string ('read', 'dismiss', 'delete')
    """
    try:
        data = request.get_json()
        
        if not data or 'notification_ids' not in data or 'action' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing notification_ids or action'
            }), 400
        
        notification_ids = data['notification_ids']
        action = data['action']
        
        if action not in ['read', 'dismiss', 'delete']:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Must be: read, dismiss, or delete'
            }), 400
        
        query = Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id
        )
        
        if action == 'read':
            count = query.update({
                'is_read': True,
                'read_at': datetime.utcnow()
            }, synchronize_session=False)
            
        elif action == 'dismiss':
            count = query.update({
                'is_dismissed': True
            }, synchronize_session=False)
            
        elif action == 'delete':
            count = query.delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} notification(s) {action}',
            'count': count
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error performing bulk action: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HELPER ENDPOINTS - Create notifications for specific events
# ============================================================================

@notification_bp.route('/trigger/budget-check', methods=['POST'])
@login_required
def trigger_budget_check():
    """
    Manually trigger budget check for a specific budget
    Request body:
        - budget_id: int
    """
    try:
        data = request.get_json()
        
        if not data or 'budget_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing budget_id'
            }), 400
        
        from models.budget import Budget
        budget = Budget.query.filter_by(
            id=data['budget_id'],
            user_id=current_user.id
        ).first()
        
        if not budget:
            return jsonify({
                'success': False,
                'error': 'Budget not found'
            }), 404
        
        # Check and create notification if needed
        BudgetNotificationManager.check_and_notify_budget_status(budget)
        
        return jsonify({
            'success': True,
            'message': 'Budget check completed'
        })
        
    except Exception as e:
        print(f"❌ Error triggering budget check: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/trigger/monthly-summary', methods=['POST'])
@login_required
def trigger_monthly_summary():
    """
    Create monthly summary notification
    Request body:
        - month: int
        - year: int
    """
    try:
        data = request.get_json()
        month = data.get('month', datetime.now().month)
        year = data.get('year', datetime.now().year)
        
        # Calculate monthly stats
        from models.transaction import Transaction
        from models.budget import Budget
        from sqlalchemy import func, extract
        
        # Total spent
        total_spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        ).scalar() or 0
        
        # Budgets exceeded
        budgets = Budget.query.filter_by(
            month=month,
            year=year,
            user_id=current_user.id
        ).all()
        budget_exceeded_count = sum(1 for b in budgets if b.percentage_used >= 100)
        
        # Create notification
        BudgetNotificationManager.notify_monthly_summary(
            month, year, total_spent, budget_exceeded_count, current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': 'Monthly summary notification created'
        })
        
    except Exception as e:
        print(f"❌ Error creating monthly summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500