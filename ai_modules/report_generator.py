"""
Report Generator - FIXED VERSION
Save as: ai_modules/report_generator.py
"""

from models.database import db
from models.transaction import Transaction
from models.category import Category
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ReportGenerator:
    """Generate various financial reports"""
    
    @staticmethod
    def generate_monthly_report(year, month):
        """Generate monthly summary report"""
        
        # Date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Total expenses
        total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).scalar() or 0
        
        # Transaction count
        count = db.session.query(
            func.count(Transaction.id)
        ).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).scalar() or 0
        
        # Category breakdown
        category_breakdown = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).group_by(Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
        categories = [{
            'name': cat[0],
            'total': float(cat[1]),
            'count': cat[2],
            'percentage': (float(cat[1]) / total * 100) if total > 0 else 0
        } for cat in category_breakdown]
        
        # Top vendors
        top_vendors = db.session.query(
            Transaction.vendor_name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.transaction_date.between(start_date, end_date),
            Transaction.vendor_name.isnot(None)
        ).group_by(Transaction.vendor_name).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(10).all()
        
        vendors = [{
            'name': v[0],
            'total': float(v[1]),
            'count': v[2]
        } for v in top_vendors]
        
        # Daily spending - FIXED
        daily_spending = db.session.query(
            Transaction.transaction_date,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).group_by(Transaction.transaction_date).order_by(Transaction.transaction_date).all()
        
        daily = []
        for d in daily_spending:
            date_obj = d[0]
            # Handle both datetime and date objects
            if isinstance(date_obj, str):
                date_str = date_obj
            elif hasattr(date_obj, 'strftime'):
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = str(date_obj)
            
            daily.append({
                'date': date_str,
                'total': float(d[1])
            })
        
        # Average transaction
        avg_transaction = total / count if count > 0 else 0
        
        # Payment method breakdown
        payment_methods = db.session.query(
            Transaction.payment_method,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.transaction_date.between(start_date, end_date),
            Transaction.payment_method.isnot(None)
        ).group_by(Transaction.payment_method).all()
        
        payments = [{
            'method': p[0],
            'total': float(p[1]),
            'count': p[2],
            'percentage': (float(p[1]) / total * 100) if total > 0 else 0
        } for p in payment_methods]
        
        # Tax summary
        total_tax = db.session.query(
            func.sum(Transaction.tax_amount)
        ).filter(
            Transaction.transaction_date.between(start_date, end_date),
            Transaction.tax_amount.isnot(None)
        ).scalar() or 0
        
        return {
            'period': {
                'type': 'monthly',
                'year': year,
                'month': month,
                'month_name': start_date.strftime('%B'),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_expenses': float(total),
                'transaction_count': count,
                'average_transaction': float(avg_transaction),
                'total_tax': float(total_tax),
                'days_in_period': (end_date - start_date).days + 1,
                'average_daily': float(total / ((end_date - start_date).days + 1)) if (end_date - start_date).days + 1 > 0 else 0
            },
            'categories': categories,
            'vendors': vendors,
            'daily_spending': daily,
            'payment_methods': payments
        }
    
    @staticmethod
    def generate_quarterly_report(year, quarter):
        """Generate quarterly report"""
        
        # Determine quarter months
        quarter_months = {
            1: (1, 2, 3),
            2: (4, 5, 6),
            3: (7, 8, 9),
            4: (10, 11, 12)
        }
        
        months = quarter_months.get(quarter, (1, 2, 3))
        start_month = months[0]
        end_month = months[2]
        
        start_date = datetime(year, start_month, 1)
        if end_month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
        
        # Get monthly breakdown for the quarter
        monthly_data = []
        for month in months:
            month_report = ReportGenerator.generate_monthly_report(year, month)
            monthly_data.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'total': month_report['summary']['total_expenses'],
                'count': month_report['summary']['transaction_count']
            })
        
        # Overall quarter totals
        total = sum(m['total'] for m in monthly_data)
        count = sum(m['count'] for m in monthly_data)
        
        # Category breakdown for quarter
        category_breakdown = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).group_by(Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
        categories = [{
            'name': cat[0],
            'total': float(cat[1]),
            'count': cat[2],
            'percentage': (float(cat[1]) / total * 100) if total > 0 else 0
        } for cat in category_breakdown]
        
        return {
            'period': {
                'type': 'quarterly',
                'year': year,
                'quarter': quarter,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_expenses': float(total),
                'transaction_count': count,
                'average_monthly': float(total / 3) if total > 0 else 0,
                'days_in_period': (end_date - start_date).days + 1
            },
            'monthly_breakdown': monthly_data,
            'categories': categories
        }
    
    @staticmethod
    def generate_comparison_report(period_type='monthly', periods=6):
        """Generate comparison report for multiple periods"""
        
        now = datetime.now()
        periods_data = []
        
        if period_type == 'monthly':
            for i in range(periods):
                date = now - relativedelta(months=i)
                report = ReportGenerator.generate_monthly_report(date.year, date.month)
                periods_data.append({
                    'period': f"{date.strftime('%B %Y')}",
                    'total': report['summary']['total_expenses'],
                    'count': report['summary']['transaction_count'],
                    'avg_transaction': report['summary']['average_transaction']
                })
        
        elif period_type == 'quarterly':
            for i in range(periods):
                date = now - relativedelta(months=i*3)
                quarter = (date.month - 1) // 3 + 1
                report = ReportGenerator.generate_quarterly_report(date.year, quarter)
                periods_data.append({
                    'period': f"Q{quarter} {date.year}",
                    'total': report['summary']['total_expenses'],
                    'count': report['summary']['transaction_count'],
                    'avg_transaction': 0  # Add default
                })
        
        # Reverse to show oldest first
        periods_data.reverse()
        
        # Calculate trends
        if len(periods_data) > 1:
            latest = periods_data[-1]['total']
            previous = periods_data[-2]['total']
            change = ((latest - previous) / previous * 100) if previous > 0 else 0
        else:
            change = 0
        
        return {
            'period_type': period_type,
            'periods_count': periods,
            'data': periods_data,
            'trend': {
                'change_percentage': float(change),
                'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
            }
        }
    
    @staticmethod
    def generate_custom_report(start_date, end_date):
        """Generate report for custom date range"""
        
        # Ensure dates are datetime objects
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Total expenses
        total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).scalar() or 0
        
        # Transaction count
        count = db.session.query(
            func.count(Transaction.id)
        ).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).scalar() or 0
        
        # Category breakdown
        category_breakdown = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).group_by(Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
        categories = [{
            'name': cat[0],
            'total': float(cat[1]),
            'count': cat[2],
            'percentage': (float(cat[1]) / total * 100) if total > 0 else 0
        } for cat in category_breakdown]
        
        days = (end_date - start_date).days + 1
        
        return {
            'period': {
                'type': 'custom',
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            },
            'summary': {
                'total_expenses': float(total),
                'transaction_count': count,
                'average_daily': float(total / days) if days > 0 else 0,
                'average_transaction': float(total / count) if count > 0 else 0
            },
            'categories': categories,
            'vendors': [],  # Add empty vendors list
            'daily_spending': []  # Add empty daily spending
        }