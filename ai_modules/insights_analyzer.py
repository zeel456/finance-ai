"""
Advanced Financial Insights Analyzer
ML-powered spending pattern analysis, anomaly detection, and predictive insights
Save as: ai_modules/insights_analyzer.py
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from models.transaction import Transaction
from models.category import Category
from models.budget import Budget
from models.database import db
from sqlalchemy import func, extract
import warnings
warnings.filterwarnings('ignore')


class AdvancedInsightsAnalyzer:
    """Advanced analytics for financial insights using ML"""
    
    @staticmethod
    def get_spending_patterns(months=6):
        """Analyze spending patterns using clustering"""
        try:
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            transactions = Transaction.query.filter(
                Transaction.transaction_date >= cutoff_date
            ).all()
            
            if len(transactions) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 10 transactions for analysis'
                }
            
            # Create features
            features = []
            for t in transactions:
                features.append([
                    t.amount,
                    t.transaction_date.weekday(),
                    t.transaction_date.day,
                    t.category_id if t.category_id else 0
                ])
            
            X = np.array(features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Cluster
            n_clusters = min(5, len(transactions) // 3)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Analyze
            patterns = []
            for i in range(n_clusters):
                cluster_trans = [t for j, t in enumerate(transactions) if clusters[j] == i]
                if not cluster_trans:
                    continue
                
                avg_amount = np.mean([t.amount for t in cluster_trans])
                category_counts = {}
                for t in cluster_trans:
                    cat_name = t.category.name if t.category else 'Uncategorized'
                    category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
                
                dominant = max(category_counts.items(), key=lambda x: x[1])[0]
                patterns.append({
                    'pattern_id': i + 1,
                    'transaction_count': len(cluster_trans),
                    'avg_amount': round(avg_amount, 2),
                    'dominant_category': dominant,
                    'frequency': round(len(cluster_trans) / len(transactions) * 100, 2)
                })
            
            return {
                'status': 'success',
                'total_transactions': len(transactions),
                'patterns': sorted(patterns, key=lambda x: x['transaction_count'], reverse=True),
                'analysis_period_months': months
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def detect_anomalies(sensitivity='medium'):
        """Detect anomalous transactions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=180)
            transactions = Transaction.query.filter(
                Transaction.transaction_date >= cutoff_date
            ).all()
            
            if len(transactions) < 20:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 20 transactions'
                }
            
            # Calculate stats
            category_stats = {}
            for t in transactions:
                cat_id = t.category_id if t.category_id else 0
                if cat_id not in category_stats:
                    category_stats[cat_id] = []
                category_stats[cat_id].append(t.amount)
            
            for cat_id in category_stats:
                amounts = category_stats[cat_id]
                category_stats[cat_id] = {
                    'mean': np.mean(amounts),
                    'std': np.std(amounts),
                    'max': np.max(amounts)
                }
            
            # Create features
            features = []
            transaction_refs = []
            for t in transactions:
                cat_id = t.category_id if t.category_id else 0
                cat_mean = category_stats[cat_id]['mean']
                cat_std = category_stats[cat_id]['std']
                
                features.append([
                    t.amount,
                    (t.amount - cat_mean) / (cat_std + 1e-6),
                    t.transaction_date.weekday(),
                    len(t.vendor_name) if t.vendor_name else 0
                ])
                transaction_refs.append(t)
            
            X = np.array(features)
            
            # Contamination
            contamination_map = {'low': 0.05, 'medium': 0.10, 'high': 0.15}
            contamination = contamination_map.get(sensitivity, 0.10)
            
            # Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            predictions = iso_forest.fit_predict(X)
            anomaly_scores = iso_forest.score_samples(X)
            
            # Get anomalies
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:
                    t = transaction_refs[i]
                    cat_id = t.category_id if t.category_id else 0
                    
                    reasons = []
                    if t.amount > category_stats[cat_id]['mean'] + 2 * category_stats[cat_id]['std']:
                        reasons.append('Unusually high amount')
                    if t.amount > category_stats[cat_id]['max'] * 0.8:
                        reasons.append('Near maximum spending')
                    
                    anomalies.append({
                        'transaction_id': t.id,
                        'date': t.transaction_date.strftime('%Y-%m-%d'),
                        'amount': t.amount,
                        'vendor': t.vendor_name,
                        'category': t.category.name if t.category else 'Uncategorized',
                        'anomaly_score': round(abs(score) * 100, 2),
                        'reasons': reasons if reasons else ['Unusual pattern detected'],
                        'severity': 'high' if abs(score) > 0.6 else 'medium'
                    })
            
            anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
            
            return {
                'status': 'success',
                'anomaly_count': len(anomalies),
                'anomalies': anomalies[:20],
                'sensitivity': sensitivity,
                'analysis_period': '6 months'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def forecast_spending(category_id=None, months=3):
        """Forecast future spending"""
        try:
            cutoff_date = datetime.now() - timedelta(days=365)
            query = Transaction.query.filter(Transaction.transaction_date >= cutoff_date)
            if category_id:
                query = query.filter(Transaction.category_id == category_id)
            
            transactions = query.all()
            
            if len(transactions) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 10 transactions'
                }
            
            # Group by month
            monthly_spending = {}
            for t in transactions:
                month_key = f"{t.transaction_date.year}-{t.transaction_date.month:02d}"
                monthly_spending[month_key] = monthly_spending.get(month_key, 0) + t.amount
            
            sorted_months = sorted(monthly_spending.keys())
            spending_values = [monthly_spending[m] for m in sorted_months]
            
            if len(spending_values) < 3:
                return {'status': 'insufficient_data', 'message': 'Need at least 3 months'}
            
            # Moving average
            window_size = min(3, len(spending_values))
            recent_avg = np.mean(spending_values[-window_size:])
            
            # Trend
            if len(spending_values) >= 6:
                recent_half = spending_values[len(spending_values)//2:]
                older_half = spending_values[:len(spending_values)//2]
                trend = (np.mean(recent_half) - np.mean(older_half)) / np.mean(older_half)
            else:
                trend = 0
            
            # Forecast
            forecasts = []
            current_date = datetime.now()
            for i in range(1, months + 1):
                forecast_date = current_date + timedelta(days=30 * i)
                forecast_value = recent_avg * (1 + trend * i * 0.1)
                std_dev = np.std(spending_values)
                
                forecasts.append({
                    'month': forecast_date.strftime('%B %Y'),
                    'predicted_amount': round(forecast_value, 2),
                    'lower_bound': round(max(0, forecast_value - std_dev), 2),
                    'upper_bound': round(forecast_value + std_dev, 2),
                    'confidence': 'medium' if len(spending_values) >= 6 else 'low'
                })
            
            return {
                'status': 'success',
                'historical_average': round(np.mean(spending_values), 2),
                'trend': 'increasing' if trend > 0.05 else 'decreasing' if trend < -0.05 else 'stable',
                'trend_percentage': round(trend * 100, 2),
                'forecasts': forecasts,
                'category': Category.query.get(category_id).name if category_id else 'All Categories'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def get_savings_recommendations():
        """Generate savings recommendations"""
        try:
            cutoff_date = datetime.now() - timedelta(days=90)
            transactions = Transaction.query.filter(
                Transaction.transaction_date >= cutoff_date
            ).all()
            
            if not transactions:
                return {'status': 'insufficient_data', 'message': 'No recent transactions'}
            
            recommendations = []
            categories = Category.query.all()
            
            for category in categories:
                cat_trans = [t for t in transactions if t.category_id == category.id]
                if not cat_trans:
                    continue
                
                total_spent = sum(t.amount for t in cat_trans)
                monthly_spent = total_spent / 3
                
                # High spending
                if total_spent > 10000:
                    potential_savings = total_spent * 0.15
                    recommendations.append({
                        'category': category.name,
                        'type': 'high_spending',
                        'priority': 'high',
                        'message': f'Consider reducing {category.name} expenses',
                        'current_monthly': round(monthly_spent, 2),
                        'potential_savings': round(potential_savings / 3, 2),
                        'suggestion': f'Try to reduce spending by 15% to save ₹{round(potential_savings / 3, 2)} per month'
                    })
                
                # Over budget
                current_month = datetime.now().month
                current_year = datetime.now().year
                budget = Budget.query.filter_by(
                    category_id=category.id,
                    month=current_month,
                    year=current_year
                ).first()
                
                if budget and monthly_spent > budget.amount:
                    overage = monthly_spent - budget.amount
                    recommendations.append({
                        'category': category.name,
                        'type': 'over_budget',
                        'priority': 'critical',
                        'message': f'Over budget in {category.name}',
                        'current_monthly': round(monthly_spent, 2),
                        'budget': budget.amount,
                        'overage': round(overage, 2),
                        'suggestion': f'You\'re over budget by ₹{round(overage, 2)}. Review your {category.name} expenses.'
                    })
                
                # High frequency
                if len(cat_trans) > 30:
                    avg_per_trans = total_spent / len(cat_trans)
                    recommendations.append({
                        'category': category.name,
                        'type': 'high_frequency',
                        'priority': 'medium',
                        'message': f'Frequent {category.name} transactions',
                        'transaction_count': len(cat_trans),
                        'avg_amount': round(avg_per_trans, 2),
                        'suggestion': f'Consider bulk purchases to reduce {len(cat_trans)} small transactions'
                    })
            
            # General
            total_spending = sum(t.amount for t in transactions)
            monthly_avg = total_spending / 3
            
            if monthly_avg > 50000:
                recommendations.append({
                    'category': 'Overall',
                    'type': 'general',
                    'priority': 'medium',
                    'message': 'High overall spending detected',
                    'current_monthly': round(monthly_avg, 2),
                    'potential_savings': round(monthly_avg * 0.10, 2),
                    'suggestion': f'A 10% reduction could save ₹{round(monthly_avg * 0.10, 2)} per month'
                })
            
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: priority_order[x['priority']])
            
            return {
                'status': 'success',
                'recommendation_count': len(recommendations),
                'recommendations': recommendations[:10],
                'total_analyzed_transactions': len(transactions),
                'analysis_period': '3 months'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def get_category_insights(category_id, months=6):
        """Deep dive analytics for a category"""
        try:
            category = db.session.get(Category, category_id)
            if not category:
                return {'status': 'error', 'message': 'Category not found'}
            
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            transactions = Transaction.query.filter(
                Transaction.category_id == category_id,
                Transaction.transaction_date >= cutoff_date
            ).all()
            
            if not transactions:
                return {'status': 'no_data', 'message': f'No transactions for {category.name}'}
            
            amounts = [t.amount for t in transactions]
            total_spent = sum(amounts)
            
            # Vendor analysis
            vendor_spending = {}
            for t in transactions:
                vendor = t.vendor_name if t.vendor_name else 'Unknown'
                vendor_spending[vendor] = vendor_spending.get(vendor, 0) + t.amount
            
            top_vendors = sorted(vendor_spending.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Weekday analysis
            weekday_spending = [0] * 7
            for t in transactions:
                weekday_spending[t.transaction_date.weekday()] += t.amount
            
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            spending_by_day = [
                {'day': weekdays[i], 'amount': round(weekday_spending[i], 2)}
                for i in range(7)
            ]
            
            # Monthly trend
            monthly_data = {}
            for t in transactions:
                month_key = t.transaction_date.strftime('%Y-%m')
                monthly_data[month_key] = monthly_data.get(month_key, 0) + t.amount
            
            trend_data = [
                {'month': k, 'amount': round(v, 2)}
                for k, v in sorted(monthly_data.items())
            ]
            
            return {
                'status': 'success',
                'category': category.name,
                'summary': {
                    'total_spent': round(total_spent, 2),
                    'transaction_count': len(transactions),
                    'avg_transaction': round(np.mean(amounts), 2),
                    'median_transaction': round(np.median(amounts), 2),
                    'std_deviation': round(np.std(amounts), 2),
                    'highest_transaction': round(max(amounts), 2),
                    'lowest_transaction': round(min(amounts), 2)
                },
                'top_vendors': [
                    {'vendor': v, 'amount': round(a, 2), 'percentage': round(a/total_spent*100, 1)}
                    for v, a in top_vendors
                ],
                'spending_by_weekday': spending_by_day,
                'monthly_trend': trend_data,
                'analysis_period_months': months
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}