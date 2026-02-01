"""
Budget Utilities
Automatically sync budget spending when transactions are added/modified
✅ NOW WITH NOTIFICATION INTEGRATION
"""

from models.database import db
from models.budget import Budget
from models.transaction import Transaction
from sqlalchemy import extract, func
from datetime import datetime


class BudgetUtils:
    """Utility functions for budget management"""
    
    @staticmethod
    def sync_budget_spending(category_id, month, year):
        """
        Sync spent amount for a specific budget
        
        Args:
            category_id: Category ID
            month: Month (1-12)
            year: Year
            
        Returns:
            Updated budget or None
        """
        try:
            # Find budget
            budget = Budget.query.filter_by(
                category_id=category_id,
                month=month,
                year=year
            ).first()
            
            if not budget:
                return None
            
            # Calculate actual spending
            spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.category_id == category_id,
                extract('month', Transaction.transaction_date) == month,
                extract('year', Transaction.transaction_date) == year
            ).scalar()
            
            # Update budget
            budget.spent = spent if spent else 0.0
            db.session.commit()
            
            # ✅ NOTIFICATION: Check budget status after sync
            try:
                from models.notification_system import BudgetNotificationManager
                BudgetNotificationManager.check_and_notify_budget_status(budget)
            except Exception as e:
                print(f"⚠️ Notification error (non-critical): {e}")
            
            return budget
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error syncing budget: {e}")
            return None
    
    @staticmethod
    def sync_all_budgets():
        """Sync all budgets with current spending"""
        try:
            budgets = Budget.query.all()
            updated_count = 0
            
            for budget in budgets:
                spent = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.category_id == budget.category_id,
                    extract('month', Transaction.transaction_date) == budget.month,
                    extract('year', Transaction.transaction_date) == budget.year
                ).scalar()
                
                budget.spent = spent if spent else 0.0
                updated_count += 1
                
                # ✅ NOTIFICATION: Check each budget status
                try:
                    from models.notification_system import BudgetNotificationManager
                    BudgetNotificationManager.check_and_notify_budget_status(budget)
                except Exception as e:
                    print(f"⚠️ Notification error for budget {budget.id}: {e}")
            
            db.session.commit()
            print(f"✅ Synced {updated_count} budgets")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error syncing all budgets: {e}")
            return 0
    
    @staticmethod
    def auto_create_budgets_from_history(month, year, lookback_months=3):
        """
        Auto-create budgets based on historical spending
        
        Args:
            month: Target month
            year: Target year
            lookback_months: Number of past months to analyze
            
        Returns:
            List of created budgets
        """
        try:
            from models.category import Category
            
            created_budgets = []
            categories = Category.query.all()
            
            for category in categories:
                # Check if budget already exists
                existing = Budget.query.filter_by(
                    category_id=category.id,
                    month=month,
                    year=year
                ).first()
                
                if existing:
                    continue
                
                # Calculate average spending from past months
                total_spending = 0
                count = 0
                
                for i in range(1, lookback_months + 1):
                    past_month = month - i
                    past_year = year
                    
                    if past_month < 1:
                        past_month += 12
                        past_year -= 1
                    
                    spent = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.category_id == category.id,
                        extract('month', Transaction.transaction_date) == past_month,
                        extract('year', Transaction.transaction_date) == past_year
                    ).scalar()
                    
                    if spent:
                        total_spending += spent
                        count += 1
                
                if count > 0:
                    # Create budget with 10% buffer
                    avg_spending = total_spending / count
                    suggested_budget = avg_spending * 1.1
                    
                    # Calculate current spending
                    current_spent = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.category_id == category.id,
                        extract('month', Transaction.transaction_date) == month,
                        extract('year', Transaction.transaction_date) == year
                    ).scalar()
                    
                    budget = Budget(
                        category_id=category.id,
                        month=month,
                        year=year,
                        amount=round(suggested_budget, 2),
                        spent=current_spent if current_spent else 0.0
                    )
                    
                    db.session.add(budget)
                    created_budgets.append(budget)
            
            db.session.commit()
            
            # ✅ NOTIFICATION: Notify about auto-created budgets
            if created_budgets:
                try:
                    from models.notification_system import NotificationManager
                    NotificationManager.create_notification(
                        type='budget_auto_created',
                        severity='info',
                        title='📊 Budgets Auto-Created',
                        message=f'{len(created_budgets)} budget(s) automatically created based on your spending history',
                        action_url='/budgets',
                        action_label='View Budgets'
                    )
                    print(f"✅ Notification sent: {len(created_budgets)} budgets auto-created")
                except Exception as e:
                    print(f"⚠️ Notification error: {e}")
            
            return created_budgets
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error auto-creating budgets: {e}")
            return []
    
    @staticmethod
    def get_budget_health(month=None, year=None):
        """
        Get overall budget health score
        
        Returns:
            Dictionary with health metrics
        """
        try:
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            budgets = Budget.query.filter_by(month=month, year=year).all()
            
            if not budgets:
                return {
                    'score': 0,
                    'status': 'no_budgets',
                    'message': 'No budgets set for this period'
                }
            
            total_budget = sum(b.amount for b in budgets)
            total_spent = sum(b.spent for b in budgets)
            
            if total_budget == 0:
                return {
                    'score': 0,
                    'status': 'invalid',
                    'message': 'Invalid budget configuration'
                }
            
            usage_percentage = (total_spent / total_budget) * 100
            over_budget_count = sum(1 for b in budgets if b.spent > b.amount)
            
            # Calculate health score (0-100)
            if usage_percentage <= 80:
                score = 100
                status = 'excellent'
                message = 'Great job! You\'re well within budget'
            elif usage_percentage <= 95:
                score = 80
                status = 'good'
                message = 'You\'re on track with your budget'
            elif usage_percentage <= 100:
                score = 60
                status = 'caution'
                message = 'Approaching budget limit'
            else:
                score = max(0, 40 - (usage_percentage - 100))
                status = 'warning'
                message = f'Over budget in {over_budget_count} categories'
            
            return {
                'score': round(score, 1),
                'status': status,
                'message': message,
                'usage_percentage': round(usage_percentage, 1),
                'total_budget': total_budget,
                'total_spent': total_spent,
                'over_budget_count': over_budget_count
            }
            
        except Exception as e:
            print(f"❌ Error calculating budget health: {e}")
            return {
                'score': 0,
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def get_budget_recommendations(category_id, month, year):
        """
        Get smart budget recommendations for a category
        
        Returns:
            Dictionary with recommendations
        """
        try:
            from models.category import Category
            
            category = db.session.get(Category, category_id)
            if not category:
                return None
            
            # Get historical spending (last 6 months)
            spending_history = []
            
            for i in range(6):
                past_month = month - i
                past_year = year
                
                if past_month < 1:
                    past_month += 12
                    past_year -= 1
                
                spent = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.category_id == category_id,
                    extract('month', Transaction.transaction_date) == past_month,
                    extract('year', Transaction.transaction_date) == past_year
                ).scalar()
                
                spending_history.append(spent if spent else 0.0)
            
            avg_spending = sum(spending_history) / len(spending_history)
            max_spending = max(spending_history)
            min_spending = min(spending_history)
            
            # Calculate trend
            if len(spending_history) >= 2:
                recent_avg = sum(spending_history[:3]) / 3
                older_avg = sum(spending_history[3:]) / 3
                trend = 'increasing' if recent_avg > older_avg * 1.1 else 'decreasing' if recent_avg < older_avg * 0.9 else 'stable'
            else:
                trend = 'insufficient_data'
            
            # Generate recommendations
            recommendations = []
            
            if trend == 'increasing':
                recommended_budget = avg_spending * 1.2
                recommendations.append(f"Spending is trending up. Consider a budget of ₹{recommended_budget:.0f}")
            elif trend == 'decreasing':
                recommended_budget = avg_spending * 1.1
                recommendations.append(f"Spending is trending down. Budget of ₹{recommended_budget:.0f} should be sufficient")
            else:
                recommended_budget = avg_spending * 1.15
                recommendations.append(f"Spending is stable. Suggested budget: ₹{recommended_budget:.0f}")
            
            # Add volatility warning
            if max_spending > avg_spending * 2:
                recommendations.append("⚠️ High volatility detected. Consider adding a buffer")
            
            return {
                'category_name': category.name,
                'recommended_budget': round(recommended_budget, 2),
                'avg_spending': round(avg_spending, 2),
                'max_spending': round(max_spending, 2),
                'min_spending': round(min_spending, 2),
                'trend': trend,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return None
        
    @staticmethod
    def sync_transaction_budgets(transaction, old_category_id=None, old_date=None):
        """
        Sync budgets affected by a transaction operation
        ✅ NOW WITH NOTIFICATION SUPPORT
        
        Args:
            transaction: Transaction object (new or updated)
            old_category_id: Previous category (for updates)
            old_date: Previous date (for updates)
        
        This handles:
        - New transactions: Sync the target budget
        - Updated transactions: Sync both old and new budgets (if changed)
        - Deleted transactions: Sync the source budget
        """
        try:
            budgets_to_sync = set()  # Use set to avoid duplicates
            
            # Current transaction budget
            if transaction.category_id and transaction.transaction_date:
                budgets_to_sync.add((
                    transaction.category_id,
                    transaction.transaction_date.month,
                    transaction.transaction_date.year
                ))
            
            # Previous budget (if transaction was moved)
            if old_category_id and old_date:
                budgets_to_sync.add((
                    old_category_id,
                    old_date.month,
                    old_date.year
                ))
            
            # Sync all affected budgets
            synced_budgets = []
            for category_id, month, year in budgets_to_sync:
                budget = BudgetUtils.sync_budget_spending(category_id, month, year)
                if budget:
                    synced_budgets.append(budget)
                    print(f"✅ Budget synced: {budget.category.name if budget.category else 'Unknown'} - {month}/{year}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error syncing transaction budgets: {e}")
            import traceback
            traceback.print_exc()
            return False


    @staticmethod
    def sync_deleted_transaction_budget(category_id, transaction_date):
        """
        Sync budget after a transaction is deleted
        ✅ NOW WITH NOTIFICATION SUPPORT
        
        Args:
            category_id: Category of deleted transaction
            transaction_date: Date of deleted transaction
        """
        if category_id and transaction_date:
            budget = BudgetUtils.sync_budget_spending(
                category_id,
                transaction_date.month,
                transaction_date.year
            )
            
            if budget:
                print(f"✅ Budget synced after deletion: {budget.category.name if budget.category else 'Unknown'}")
            
            return budget
        return False
    
    @staticmethod
    def check_budget_alerts(month=None, year=None):
        """
        Manually check all budgets and create alerts if needed
        Useful for batch operations or scheduled tasks
        
        Args:
            month: Month to check (default: current month)
            year: Year to check (default: current year)
            
        Returns:
            Number of alerts created
        """
        try:
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            budgets = Budget.query.filter_by(month=month, year=year).all()
            alerts_created = 0
            
            for budget in budgets:
                try:
                    from models.notification_system import BudgetNotificationManager
                    BudgetNotificationManager.check_and_notify_budget_status(budget)
                    
                    # Check if alert should be created (75%+)
                    if budget.percentage_used >= 75:
                        alerts_created += 1
                        
                except Exception as e:
                    print(f"⚠️ Error checking budget {budget.id}: {e}")
            
            print(f"✅ Checked {len(budgets)} budgets, created {alerts_created} alerts")
            return alerts_created
            
        except Exception as e:
            print(f"❌ Error checking budget alerts: {e}")
            return 0
    
    @staticmethod
    def get_overspending_categories(month=None, year=None):
        """
        Get list of categories that are over budget
        
        Returns:
            List of dictionaries with overspending details
        """
        try:
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            budgets = Budget.query.filter_by(month=month, year=year).all()
            
            overspending = []
            for budget in budgets:
                if budget.spent > budget.amount:
                    overspending.append({
                        'category_id': budget.category_id,
                        'category_name': budget.category.name if budget.category else 'Unknown',
                        'budget_amount': budget.amount,
                        'spent': budget.spent,
                        'overspent': budget.spent - budget.amount,
                        'percentage': budget.percentage_used
                    })
            
            # Sort by overspent amount (highest first)
            overspending.sort(key=lambda x: x['overspent'], reverse=True)
            
            return overspending
            
        except Exception as e:
            print(f"❌ Error getting overspending categories: {e}")
            return []
    
    @staticmethod
    def get_budget_summary(month=None, year=None):
        """
        Get comprehensive budget summary with all metrics
        
        Returns:
            Dictionary with complete budget summary
        """
        try:
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            budgets = Budget.query.filter_by(month=month, year=year).all()
            
            if not budgets:
                return {
                    'total_budget': 0,
                    'total_spent': 0,
                    'total_remaining': 0,
                    'percentage_used': 0,
                    'budget_count': 0,
                    'over_budget_count': 0,
                    'within_budget_count': 0,
                    'approaching_limit_count': 0,
                    'health': BudgetUtils.get_budget_health(month, year)
                }
            
            total_budget = sum(b.amount for b in budgets)
            total_spent = sum(b.spent for b in budgets)
            total_remaining = total_budget - total_spent
            
            percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            over_budget_count = sum(1 for b in budgets if b.percentage_used >= 100)
            approaching_limit_count = sum(1 for b in budgets if 75 <= b.percentage_used < 100)
            within_budget_count = len(budgets) - over_budget_count - approaching_limit_count
            
            return {
                'total_budget': round(total_budget, 2),
                'total_spent': round(total_spent, 2),
                'total_remaining': round(total_remaining, 2),
                'percentage_used': round(percentage_used, 1),
                'budget_count': len(budgets),
                'over_budget_count': over_budget_count,
                'within_budget_count': within_budget_count,
                'approaching_limit_count': approaching_limit_count,
                'health': BudgetUtils.get_budget_health(month, year)
            }
            
        except Exception as e:
            print(f"❌ Error getting budget summary: {e}")
            return None