"""
Advanced Insights Routes
API endpoints for ML-powered financial insights
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ai_modules.insights_analyzer import AdvancedInsightsAnalyzer

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')


@insights_bp.route('/patterns', methods=['GET'])
@login_required
def get_spending_patterns():
    """Get spending pattern analysis"""
    try:
        months = request.args.get('months', 6, type=int)
        
        if not 1 <= months <= 12:
            return jsonify({
                'success': False,
                'error': 'Months must be between 1 and 12'
            }), 400
        
        result = AdvancedInsightsAnalyzer.get_spending_patterns(months, current_user.id)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@insights_bp.route('/anomalies', methods=['GET'])
@login_required
def detect_anomalies():
    """Detect anomalous transactions"""
    try:
        sensitivity = request.args.get('sensitivity', 'medium')
        
        if sensitivity not in ['low', 'medium', 'high']:
            return jsonify({
                'success': False,
                'error': 'Sensitivity must be low, medium, or high'
            }), 400
        
        result = AdvancedInsightsAnalyzer.detect_anomalies(sensitivity, current_user.id)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@insights_bp.route('/forecast', methods=['GET'])
@login_required
def forecast_spending():
    """Forecast future spending"""
    try:
        category_id = request.args.get('category_id', type=int)
        months = request.args.get('months', 3, type=int)
        
        if not 1 <= months <= 12:
            return jsonify({
                'success': False,
                'error': 'Months must be between 1 and 12'
            }), 400
        
        result = AdvancedInsightsAnalyzer.forecast_spending(category_id, months, current_user.id)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@insights_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """Get AI-powered savings recommendations"""
    try:
        result = AdvancedInsightsAnalyzer.get_savings_recommendations(current_user.id)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@insights_bp.route('/category/<int:category_id>', methods=['GET'])
@login_required
def get_category_insights(category_id):
    """Get deep insights for a specific category"""
    try:
        months = request.args.get('months', 6, type=int)
        
        result = AdvancedInsightsAnalyzer.get_category_insights(category_id, months, current_user.id)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@insights_bp.route('/dashboard', methods=['GET'])
@login_required
def get_insights_dashboard():
    """Get comprehensive insights dashboard data"""
    try:
        # Get all insights
        patterns = AdvancedInsightsAnalyzer.get_spending_patterns(months=6, user_id=current_user.id)
        anomalies = AdvancedInsightsAnalyzer.detect_anomalies(sensitivity='medium', user_id=current_user.id)
        forecast = AdvancedInsightsAnalyzer.forecast_spending(category_id=None, months=3, user_id=current_user.id)
        recommendations = AdvancedInsightsAnalyzer.get_savings_recommendations(current_user.id)
        
        return jsonify({
            'success': True,
            'dashboard': {
                'patterns': patterns if patterns['status'] == 'success' else None,
                'anomalies': anomalies if anomalies['status'] == 'success' else None,
                'forecast': forecast if forecast['status'] == 'success' else None,
                'recommendations': recommendations if recommendations['status'] == 'success' else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500