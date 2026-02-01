"""
Budget Management Routes
Save as: routes/budget_routes.py
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.budget import Budget
from models.category import Category
from models.transaction import Transaction
from datetime import datetime
from sqlalchemy import and_, extract, func
from utils.budget_utils import BudgetUtils


budget_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')


def calculate_spent(category_id, month, year, user_id):
    """Calculate total spent for a category in a given month/year"""
    result = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.category_id == category_id,
        Transaction.user_id == user_id,
        extract('month', Transaction.transaction_date) == month,
        extract('year', Transaction.transaction_date) == year
    ).scalar()
    
    return result if result else 0.0


@budget_bp.route('/', methods=['GET'])
@login_required
def get_budgets():
    """Get all budgets with optional filtering"""
    try:
        # Get query parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        category_id = request.args.get('category_id', type=int)
        
        # Build query
        query = Budget.query.filter_by(user_id=current_user.id)
        
        if month:
            query = query.filter(Budget.month == month)
        if year:
            query = query.filter(Budget.year == year)
        if category_id:
            query = query.filter(Budget.category_id == category_id)
        
        budgets = query.order_by(Budget.year.desc(), Budget.month.desc()).all()
        
        return jsonify({
            'success': True,
            'budgets': [budget.to_dict() for budget in budgets],
            'count': len(budgets)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/<int:budget_id>', methods=['GET'])
@login_required
def get_budget(budget_id):
    """Get a specific budget"""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        
        if not budget:
            return jsonify({
                'success': False,
                'error': 'Budget not found'
            }), 404
        
        return jsonify({
            'success': True,
            'budget': budget.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/', methods=['POST'])
@login_required
def create_budget():
    """Create a new budget"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category_id', 'month', 'year', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate month
        if not 1 <= data['month'] <= 12:
            return jsonify({
                'success': False,
                'error': 'Month must be between 1 and 12'
            }), 400
        
        # Validate amount
        if data['amount'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be greater than 0'
            }), 400
        
        # Check if category exists
        category = db.session.get(Category, data['category_id'])
        if not category:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        # Check if budget already exists
        existing = Budget.query.filter_by(
            category_id=data['category_id'],
            month=data['month'],
            year=data['year'],
            user_id=current_user.id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Budget already exists for this category and period'
            }), 400
        
        # Calculate current spending
        spent = calculate_spent(data['category_id'], data['month'], data['year'], current_user.id)
        
        # Create budget
        budget = Budget(
            category_id=data['category_id'],
            month=data['month'],
            year=data['year'],
            amount=data['amount'],
            spent=spent,
            user_id=current_user.id
        )
        
        db.session.add(budget)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Budget created successfully',
            'budget': budget.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/<int:budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    """Update an existing budget"""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        
        if not budget:
            return jsonify({
                'success': False,
                'error': 'Budget not found'
            }), 404
        
        data = request.get_json()
        
        # Update amount if provided
        if 'amount' in data:
            if data['amount'] <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Amount must be greater than 0'
                }), 400
            budget.amount = data['amount']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Budget updated successfully',
            'budget': budget.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        
        if not budget:
            return jsonify({
                'success': False,
                'error': 'Budget not found'
            }), 404
        
        db.session.delete(budget)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Budget deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/refresh-spent', methods=['POST'])
@login_required
def refresh_spent():
    """Refresh spent amounts for all budgets"""
    try:
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        updated_count = 0
        
        for budget in budgets:
            spent = calculate_spent(budget.category_id, budget.month, budget.year, current_user.id)
            if budget.spent != spent:
                budget.spent = spent
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} budgets',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/summary', methods=['GET'])
@login_required
def get_budget_summary():
    """Get budget summary for current month"""
    try:
        # Get current month/year or from params
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Get all budgets for this period
        budgets = Budget.query.filter_by(month=month, year=year, user_id=current_user.id).all()
        
        # Calculate summary
        total_budget = sum(b.amount for b in budgets)
        total_spent = sum(b.spent for b in budgets)
        total_remaining = total_budget - total_spent
        
        # Count over-budget categories
        over_budget = sum(1 for b in budgets if b.spent > b.amount)
        
        # Get categories without budgets that have spending
        all_categories = Category.query.all()
        budgeted_category_ids = {b.category_id for b in budgets}
        
        unbudgeted_spending = 0
        for category in all_categories:
            if category.id not in budgeted_category_ids:
                spent = calculate_spent(category.id, month, year, current_user.id)
                if spent > 0:
                    unbudgeted_spending += spent
        
        return jsonify({
            'success': True,
            'summary': {
                'period': {
                    'month': month,
                    'year': year
                },
                'total_budget': round(total_budget, 2),
                'total_spent': round(total_spent, 2),
                'total_remaining': round(total_remaining, 2),
                'percentage_used': round((total_spent / total_budget * 100), 2) if total_budget > 0 else 0,
                'over_budget_count': over_budget,
                'unbudgeted_spending': round(unbudgeted_spending, 2)
            },
            'budgets': [b.to_dict() for b in budgets]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/alerts', methods=['GET'])
@login_required
def get_budget_alerts():
    """Get budget alerts (over budget, near limit, etc.)"""
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        budgets = Budget.query.filter_by(month=month, year=year, user_id=current_user.id).all()
        
        alerts = []
        
        for budget in budgets:
            percentage = (budget.spent / budget.amount * 100) if budget.amount > 0 else 0
            
            if budget.spent > budget.amount:
                alerts.append({
                    'type': 'danger',
                    'category': budget.category.name,
                    'message': f'Over budget by ₹{round(budget.spent - budget.amount, 2)}',
                    'percentage': round(percentage, 2),
                    'budget': budget.to_dict()
                })
            elif percentage >= 90:
                alerts.append({
                    'type': 'warning',
                    'category': budget.category.name,
                    'message': f'{round(percentage, 1)}% of budget used',
                    'percentage': round(percentage, 2),
                    'budget': budget.to_dict()
                })
            elif percentage >= 75:
                alerts.append({
                    'type': 'info',
                    'category': budget.category.name,
                    'message': f'{round(percentage, 1)}% of budget used',
                    'percentage': round(percentage, 2),
                    'budget': budget.to_dict()
                })
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/bulk', methods=['POST'])
@login_required
def create_bulk_budgets():
    """Create budgets for multiple categories at once"""
    try:
        data = request.get_json()
        
        month = data.get('month')
        year = data.get('year')
        budgets_data = data.get('budgets', [])
        
        if not month or not year:
            return jsonify({
                'success': False,
                'error': 'Missing month or year'
            }), 400
        
        created = []
        errors = []
        
        for budget_data in budgets_data:
            try:
                category_id = budget_data.get('category_id')
                amount = budget_data.get('amount')
                
                # Check if already exists
                existing = Budget.query.filter_by(
                    category_id=category_id,
                    month=month,
                    year=year,
                    user_id=current_user.id
                ).first()
                
                if existing:
                    errors.append(f'Budget already exists for category {category_id}')
                    continue
                
                spent = calculate_spent(category_id, month, year, current_user.id)
                
                budget = Budget(
                    category_id=category_id,
                    month=month,
                    year=year,
                    amount=amount,
                    spent=spent,
                    user_id=current_user.id
                )
                
                db.session.add(budget)
                created.append(budget)
                
            except Exception as e:
                errors.append(str(e))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created)} budgets',
            'created': [b.to_dict() for b in created],
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@budget_bp.route('/auto-create', methods=['POST'])
@login_required
def auto_create_budgets():
    """Auto-create budgets based on historical spending"""
    try:
        data = request.get_json()
        month = data.get('month', datetime.now().month)
        year = data.get('year', datetime.now().year)
        lookback_months = data.get('lookback_months', 3)
        
        created = BudgetUtils.auto_create_budgets_from_history(
            month, year, lookback_months, current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created)} budgets',
            'budgets': [b.to_dict() for b in created]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/health', methods=['GET'])
@login_required
def get_budget_health():
    """Get budget health score"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        health = BudgetUtils.get_budget_health(month, year, current_user.id)
        
        return jsonify({
            'success': True,
            'health': health
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@budget_bp.route('/recommendations/<int:category_id>', methods=['GET'])
@login_required
def get_recommendations(category_id):
    """Get budget recommendations for a category"""
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        recommendations = BudgetUtils.get_budget_recommendations(
            category_id, month, year, current_user.id
        )
        
        if recommendations:
            return jsonify({
                'success': True,
                'recommendations': recommendations
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500