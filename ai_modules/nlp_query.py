import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from models.database import db
from models.transaction import Transaction
from models.category import Category
from sqlalchemy import func, extract, and_

class NLPQueryProcessor:
    """Process natural language queries about financial data"""
    
    def __init__(self):
        self.intents = {
            'total_expense': ['total', 'spent', 'spend', 'expense', 'expenses'],
            'category_expense': ['category', 'on', 'for'],
            'date_range': ['this month', 'last month', 'this year', 'today', 'yesterday', 'week'],
            'comparison': ['compare', 'vs', 'versus', 'difference', 'more than', 'less than'],
            'top_spending': ['top', 'most', 'highest', 'biggest', 'largest'],
            'vendor_analysis': ['vendor', 'merchant', 'shop', 'store', 'restaurant'],
            'budget_check': ['budget', 'limit', 'exceeded', 'over', 'remaining'],
            'tax_query': ['tax', 'gst', 'vat'],
            'payment_method': ['paid', 'payment', 'card', 'cash', 'upi'],
            'trend': ['trend', 'pattern', 'increase', 'decrease', 'growing'],
            'average_expense': ['average', 'avg', 'mean'],
            'monthly_breakdown': ['breakdown', 'distribution', 'split'],
            'prediction': ['predict', 'forecast', 'next month', 'will'],
        }
        
        self._categories = None
    
    @property
    def categories(self):
        """Lazy load categories only when needed"""
        if self._categories is None:
            try:
                self._categories = [cat.name for cat in Category.query.all()]
            except:
                # Fallback to common categories if database not available
                self._categories = [
                    'Food & Dining', 'Groceries', 'Transportation', 'Travel',
                    'Shopping', 'Entertainment', 'Healthcare', 'Education',
                    'Bills & Utilities', 'Fuel'
                ]
        return self._categories
    
    def detect_intent(self, query):
        """Detect the primary intent of the query"""
        query_lower = query.lower()
        detected_intents = []
        
        for intent, keywords in self.intents.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Return the most specific intent
        if 'comparison' in detected_intents:
            return 'comparison'
        elif 'top_spending' in detected_intents:
            return 'top_spending'
        elif 'category_expense' in detected_intents:
            return 'category_expense'
        elif 'vendor_analysis' in detected_intents:
            return 'vendor_analysis'
        elif 'budget_check' in detected_intents:
            return 'budget_check'
        elif 'tax_query' in detected_intents:
            return 'tax_query'
        elif 'payment_method' in detected_intents:
            return 'payment_method'
        elif 'trend' in detected_intents:
            return 'trend'
        elif 'total_expense' in detected_intents:
            return 'total_expense'
        else:
            return 'unknown'
    
    def extract_category(self, query):
        """Extract category from query"""
        query_lower = query.lower()
        
        for category in self.categories:
            if category.lower() in query_lower:
                return category
        
        # Check for common category keywords
        category_keywords = {
            'food': 'Food & Dining',
            'dining': 'Food & Dining',
            'restaurant': 'Food & Dining',
            'transport': 'Transportation',
            'travel': 'Travel',
            'shopping': 'Shopping',
            'entertainment': 'Entertainment',
            'utilities': 'Utilities',
            'health': 'Healthcare',
            'education': 'Education',
            'insurance': 'Insurance'
        }
        
        for keyword, category in category_keywords.items():
            if keyword in query_lower:
                return category
        
        return None
    
    def extract_date_range(self, query):
        """Extract date range from query"""
        query_lower = query.lower()
        today = datetime.now()
        
        if 'today' in query_lower:
            return today.date(), today.date()
        
        elif 'yesterday' in query_lower:
            yesterday = today - timedelta(days=1)
            return yesterday.date(), yesterday.date()
        
        elif 'this week' in query_lower:
            week_start = today - timedelta(days=today.weekday())
            return week_start.date(), today.date()
        
        elif 'last week' in query_lower:
            week_start = today - timedelta(days=today.weekday() + 7)
            week_end = week_start + timedelta(days=6)
            return week_start.date(), week_end.date()
        
        elif 'this month' in query_lower:
            month_start = today.replace(day=1)
            return month_start.date(), today.date()
        
        elif 'last month' in query_lower:
            last_month_end = today.replace(day=1) - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start.date(), last_month_end.date()
        
        elif 'this year' in query_lower:
            year_start = today.replace(month=1, day=1)
            return year_start.date(), today.date()
        
        else:
            # Try to extract specific dates
            date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
            dates = re.findall(date_pattern, query)
            
            if len(dates) >= 2:
                try:
                    start = date_parser.parse(dates[0], fuzzy=True).date()
                    end = date_parser.parse(dates[1], fuzzy=True).date()
                    return start, end
                except:
                    pass
            elif len(dates) == 1:
                try:
                    date = date_parser.parse(dates[0], fuzzy=True).date()
                    return date, date
                except:
                    pass
        
        return None, None
    
    def extract_amount(self, query):
        """Extract amount from query"""
        # Look for numbers with currency symbols or keywords
        patterns = [
            r'(?:over|above|more than|greater than)\s*(?:Rs\.?|₹)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:under|below|less than)\s*(?:Rs\.?|₹)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Rs\.?|₹)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    pass
        
        return None
    
    def process_query(self, query):
        """Main function to process a query and return results"""
        intent = self.detect_intent(query)
        
        if intent == 'total_expense':
            return self.handle_total_expense(query)
        elif intent == 'category_expense':
            return self.handle_category_expense(query)
        elif intent == 'comparison':
            return self.handle_comparison(query)
        elif intent == 'top_spending':
            return self.handle_top_spending(query)
        elif intent == 'vendor_analysis':
            return self.handle_vendor_analysis(query)
        elif intent == 'budget_check':
            return self.handle_budget_check(query)
        elif intent == 'tax_query':
            return self.handle_tax_query(query)
        elif intent == 'payment_method':
            return self.handle_payment_method(query)
        elif intent == 'trend':
            return self.handle_trend(query)
        else:
            return self.handle_unknown(query)
    
    def handle_total_expense(self, query):
        """Handle total expense queries"""
        start_date, end_date = self.extract_date_range(query)
        
        query_obj = db.session.query(func.sum(Transaction.amount))
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        total = query_obj.scalar() or 0.0
        
        return {
            'intent': 'total_expense',
            'response': f"Your {period} expenses are ₹{total:,.2f}",
            'data': {
                'total': total,
                'period': period,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'chart_type': None
        }
    
    def handle_category_expense(self, query):
        """Handle category-specific expense queries"""
        category_name = self.extract_category(query)
        start_date, end_date = self.extract_date_range(query)
        
        if not category_name:
            return {
                'intent': 'category_expense',
                'response': "I couldn't identify the category. Please specify a category like 'Food & Dining', 'Transportation', etc.",
                'data': None,
                'chart_type': None
            }
        
        category = Category.query.filter_by(name=category_name).first()
        
        if not category:
            return {
                'intent': 'category_expense',
                'response': f"Category '{category_name}' not found.",
                'data': None,
                'chart_type': None
            }
        
        query_obj = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == category.id
        )
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        total = query_obj.scalar() or 0.0
        transaction_count = Transaction.query.filter_by(category_id=category.id).count()
        
        return {
            'intent': 'category_expense',
            'response': f"Your {period} spending on {category_name} is ₹{total:,.2f} across {transaction_count} transactions.",
            'data': {
                'category': category_name,
                'total': total,
                'transaction_count': transaction_count,
                'period': period
            },
            'chart_type': None
        }
    
    def handle_comparison(self, query):
        """Handle comparison queries"""
        today = datetime.now()
        
        # This month vs last month
        this_month_start = today.replace(day=1)
        this_month_total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_date >= this_month_start.date()
        ).scalar() or 0.0
        
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        last_month_total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_date.between(last_month_start.date(), last_month_end.date())
        ).scalar() or 0.0
        
        if last_month_total > 0:
            change = ((this_month_total - last_month_total) / last_month_total) * 100
            change_text = "higher" if change > 0 else "lower"
        else:
            change = 0
            change_text = "same"
        
        return {
            'intent': 'comparison',
            'response': f"This month's expenses (₹{this_month_total:,.2f}) are {abs(change):.1f}% {change_text} than last month (₹{last_month_total:,.2f}).",
            'data': {
                'this_month': this_month_total,
                'last_month': last_month_total,
                'change_percentage': change
            },
            'chart_type': 'comparison_bar'
        }
    
    def handle_top_spending(self, query):
        """Handle top spending queries"""
        start_date, end_date = self.extract_date_range(query)
        
        # Check if asking for vendors or categories
        if 'vendor' in query.lower() or 'merchant' in query.lower():
            query_obj = db.session.query(
                Transaction.vendor_name,
                func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.vendor_name.isnot(None)
            ).group_by(Transaction.vendor_name)
        else:
            # Top categories
            query_obj = db.session.query(
                Category.name,
                func.sum(Transaction.amount).label('total')
            ).join(Transaction).group_by(Category.name)
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
        
        results = query_obj.order_by(func.sum(Transaction.amount).desc()).limit(5).all()
        
        if not results:
            return {
                'intent': 'top_spending',
                'response': "No spending data found for this period.",
                'data': None,
                'chart_type': None
            }
        
        top_items = [{'name': r[0], 'amount': r[1]} for r in results]
        
        response_text = "Here are your top 5 spending areas:\n"
        for i, item in enumerate(top_items, 1):
            response_text += f"{i}. {item['name']}: ₹{item['amount']:,.2f}\n"
        
        return {
            'intent': 'top_spending',
            'response': response_text,
            'data': {'top_items': top_items},
            'chart_type': 'top_spending_bar'
        }
    
    def handle_vendor_analysis(self, query):
        """Handle vendor-specific queries"""
        # Extract vendor name (simple approach - get capitalized words)
        words = query.split()
        vendor_candidates = [w for w in words if w[0].isupper() and len(w) > 2]
        
        if not vendor_candidates:
            # Show all vendors
            vendors = db.session.query(
                Transaction.vendor_name,
                func.sum(Transaction.amount).label('total'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.vendor_name.isnot(None)
            ).group_by(Transaction.vendor_name).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(10).all()
            
            response = "Here are your top vendors:\n"
            for v in vendors:
                response += f"• {v[0]}: ₹{v[1]:,.2f} ({v[2]} transactions)\n"
            
            return {
                'intent': 'vendor_analysis',
                'response': response,
                'data': {'vendors': [{'name': v[0], 'total': v[1], 'count': v[2]} for v in vendors]},
                'chart_type': None
            }
        
        return {
            'intent': 'vendor_analysis',
            'response': "Vendor analysis feature coming soon!",
            'data': None,
            'chart_type': None
        }
    
    def handle_budget_check(self, query):
        """Handle budget-related queries"""
        return {
            'intent': 'budget_check',
            'response': "Budget tracking feature will be available in the next phase!",
            'data': None,
            'chart_type': None
        }
    
    def handle_tax_query(self, query):
        """Handle tax-related queries"""
        start_date, end_date = self.extract_date_range(query)
        
        query_obj = db.session.query(
            func.sum(Transaction.tax_amount),
            func.sum(Transaction.amount)
        )
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        result = query_obj.first()
        total_tax = result[0] or 0.0
        total_amount = result[1] or 0.0
        
        return {
            'intent': 'tax_query',
            'response': f"Your {period} tax amount is ₹{total_tax:,.2f} on total expenses of ₹{total_amount:,.2f}.",
            'data': {
                'total_tax': total_tax,
                'total_amount': total_amount,
                'period': period
            },
            'chart_type': None
        }
    
    def handle_payment_method(self, query):
        """Handle payment method queries"""
        payment_stats = db.session.query(
            Transaction.payment_method,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.payment_method.isnot(None)
        ).group_by(Transaction.payment_method).all()
        
        if not payment_stats:
            return {
                'intent': 'payment_method',
                'response': "No payment method data available.",
                'data': None,
                'chart_type': None
            }
        
        response = "Here's your spending by payment method:\n"
        data = []
        for pm in payment_stats:
            response += f"• {pm[0]}: ₹{pm[1]:,.2f} ({pm[2]} transactions)\n"
            data.append({'method': pm[0], 'total': pm[1], 'count': pm[2]})
        
        return {
            'intent': 'payment_method',
            'response': response,
            'data': {'payment_methods': data},
            'chart_type': 'payment_pie'
        }
    
    def handle_trend(self, query):
        """Handle trend analysis queries"""
        # Get last 6 months
        today = datetime.now()
        months_data = []
        
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = today
            else:
                next_month = month_start + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(days=1)
            
            total = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_date.between(month_start.date(), month_end.date())
            ).scalar() or 0.0
            
            months_data.append({
                'month': month_start.strftime('%B'),
                'total': total
            })
        
        return {
            'intent': 'trend',
            'response': "Here's your spending trend over the last 6 months:",
            'data': {'months': months_data},
            'chart_type': 'trend_line'
        }
    
    def handle_average_expense(self, query):
        """Handle average expense queries"""
        start_date, end_date = self.extract_date_range(query)
        
        query_obj = db.session.query(
            func.avg(Transaction.amount),
            func.count(Transaction.id)
        )
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
        
        result = query_obj.first()
        avg_amount = result[0] or 0.0
        count = result[1] or 0
        
        return {
            'intent': 'average_expense',
            'response': f"Your average transaction amount is ₹{avg_amount:,.2f} across {count} transactions.",
            'data': {
                'average': avg_amount,
                'count': count
            },
            'chart_type': None
        }
    
    def handle_unknown(self, query):
        """Handle unknown queries"""
        suggestions = [
            "What's my total expense this month?",
            "How much did I spend on food?",
            "Show me top 5 spending categories",
            "Compare this month vs last month",
            "What's my tax amount this month?"
        ]
        
        return {
            'intent': 'unknown',
            'response': "I'm not sure how to answer that. Here are some questions you can ask:",
            'data': {'suggestions': suggestions},
            'chart_type': None
        }
    
    def format_period(self, start_date, end_date):
        """Format date range as readable period"""
        if start_date == end_date:
            return f"on {start_date.strftime('%B %d, %Y')}"
        else:
            return f"from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}"