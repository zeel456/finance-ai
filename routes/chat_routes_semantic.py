"""
Lightweight Chatbot - NO MEMORY CRASHES
Save as: routes/chat_routes_lightweight.py

This version works without heavy AI models to prevent OOM crashes.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.conversation import Conversation
from models.message import Message
from models.transaction import Transaction
from models.category import Category
from datetime import datetime, timedelta
from sqlalchemy import func

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def get_simple_response(query: str, user_id: int) -> dict:
    """
    Lightweight response generator - NO AI MODELS
    Works with basic keyword matching
    """
    query_lower = query.lower()
    
    # Greeting
    if any(word in query_lower for word in ['hello', 'hi', 'hey', 'morning', 'afternoon']):
        return {
            'response': f"Hello! I'm your finance assistant. Ask me about your spending, transactions, or budgets.",
            'intent': 'greeting',
            'data': None,
            'chart_type': None
        }
    
    # Help
    if 'help' in query_lower or '?' == query_lower.strip():
        return {
            'response': (
                "I can help you with:\n\n"
                "• **Total spending**: 'What's my total spending?'\n"
                "• **Category expenses**: 'How much did I spend on food?'\n"
                "• **Recent transactions**: 'Show my recent transactions'\n"
                "• **This month**: 'What did I spend this month?'\n"
                "• **Vendors**: 'Where do I shop most?'"
            ),
            'intent': 'help',
            'data': None,
            'chart_type': None
        }
    
    # Total spending
    if any(phrase in query_lower for phrase in ['total', 'all spending', 'everything', 'sum']):
        try:
            # Check if asking for specific time period
            if 'month' in query_lower:
                start_date = datetime.now().replace(day=1).date()
                end_date = datetime.now().date()
                period = "this month"
            elif 'week' in query_lower:
                start_date = (datetime.now() - timedelta(days=7)).date()
                end_date = datetime.now().date()
                period = "this week"
            elif 'year' in query_lower:
                start_date = datetime.now().replace(month=1, day=1).date()
                end_date = datetime.now().date()
                period = "this year"
            else:
                start_date = None
                end_date = None
                period = "overall"
            
            query_obj = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id
            )
            
            if start_date and end_date:
                query_obj = query_obj.filter(
                    Transaction.transaction_date.between(start_date, end_date)
                )
            
            total = query_obj.scalar() or 0.0
            
            return {
                'response': f"Your {period} total spending is **₹{total:,.2f}**.",
                'intent': 'total_expense',
                'data': {'total': total, 'period': period},
                'chart_type': 'total_bar'
            }
        except Exception as e:
            return {
                'response': f"Sorry, I couldn't calculate that. Error: {str(e)}",
                'intent': 'error',
                'data': None,
                'chart_type': None
            }
    
    # Category spending
    categories = ['food', 'transport', 'shopping', 'entertainment', 'bills', 'health', 'education', 'fuel', 'groceries', 'travel']
    for cat_keyword in categories:
        if cat_keyword in query_lower:
            try:
                # Find matching category
                category = Category.query.filter(
                    Category.name.ilike(f'%{cat_keyword}%')
                ).first()
                
                if category:
                    total = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.user_id == user_id,
                        Transaction.category_id == category.id
                    ).scalar() or 0.0
                    
                    count = db.session.query(func.count(Transaction.id)).filter(
                        Transaction.user_id == user_id,
                        Transaction.category_id == category.id
                    ).scalar() or 0
                    
                    return {
                        'response': f"You spent **₹{total:,.2f}** on {category.name} ({count} transactions).",
                        'intent': 'category_expense',
                        'data': {'category': category.name, 'total': total, 'count': count},
                        'chart_type': 'category_bar'
                    }
            except Exception as e:
                pass
    
    # Recent transactions
    if any(word in query_lower for word in ['recent', 'last', 'latest']):
        try:
            transactions = Transaction.query.filter_by(
                user_id=user_id
            ).order_by(
                Transaction.transaction_date.desc()
            ).limit(5).all()
            
            if transactions:
                trans_list = "\n".join([
                    f"• **{t.vendor_name}**: ₹{t.amount:,.2f} on {t.transaction_date.strftime('%d %b')}"
                    for t in transactions
                ])
                
                return {
                    'response': f"Your recent transactions:\n\n{trans_list}",
                    'intent': 'recent_transactions',
                    'data': {'transactions': [t.to_dict() for t in transactions]},
                    'chart_type': None
                }
            else:
                return {
                    'response': "You don't have any transactions yet. Add some transactions to get started!",
                    'intent': 'no_data',
                    'data': None,
                    'chart_type': None
                }
        except Exception as e:
            pass
    
    # Top vendors
    if any(word in query_lower for word in ['vendor', 'shop', 'store', 'merchant', 'where']):
        try:
            vendors = db.session.query(
                Transaction.vendor_name,
                func.sum(Transaction.amount).label('total'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.vendor_name.isnot(None)
            ).group_by(
                Transaction.vendor_name
            ).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(5).all()
            
            if vendors:
                vendor_list = "\n".join([
                    f"• **{v.vendor_name}**: ₹{v.total:,.2f} ({v.count} times)"
                    for v in vendors
                ])
                
                return {
                    'response': f"Your top vendors:\n\n{vendor_list}",
                    'intent': 'top_vendors',
                    'data': {'vendors': [{'name': v.vendor_name, 'total': float(v.total), 'count': v.count} for v in vendors]},
                    'chart_type': 'vendor_bar'
                }
        except Exception as e:
            pass
    
    # Default response
    return {
        'response': (
            "I'm not sure how to answer that. Try asking:\n\n"
            "• 'What's my total spending?'\n"
            "• 'How much did I spend on food?'\n"
            "• 'Show recent transactions'\n"
            "• Type 'help' for more options"
        ),
        'intent': 'unknown',
        'data': None,
        'chart_type': None
    }


@chat_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations"""
    try:
        conversations = Conversation.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Conversation.updated_at.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation(conversation_id):
    """Get a specific conversation"""
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict_detailed()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/conversations', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Conversation')
        
        conversation = Conversation(
            title=title,
            user_id=current_user.id
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Conversation deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """
    Send a message - LIGHTWEIGHT VERSION
    No AI models, no memory crashes!
    """
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        data = request.get_json()
        user_message_content = data.get('content', '').strip()
        
        if not user_message_content:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        print(f"💬 Message from user {current_user.id}: {user_message_content[:50]}...", flush=True)
        
        # 1. Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role='user',
            content=user_message_content
        )
        db.session.add(user_message)
        db.session.flush()
        
        # 2. Generate response (lightweight - no AI)
        ai_response = get_simple_response(user_message_content, current_user.id)
        
        # 3. Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=ai_response['response'],
            intent=ai_response.get('intent'),
            confidence=75.0  # Default confidence
        )
        db.session.add(assistant_message)
        
        # 4. Update conversation
        conversation.updated_at = datetime.utcnow()
        
        if not conversation.title or conversation.title == 'New Conversation':
            conversation.title = user_message_content[:50] + ('...' if len(user_message_content) > 50 else '')
        
        # 5. Commit
        db.session.commit()
        
        print(f"✅ Response generated successfully", flush=True)
        
        # 6. Return response
        return jsonify({
            'success': True,
            'user_message': user_message.to_dict(),
            'assistant_message': assistant_message.to_dict(),
            'data': ai_response.get('data'),
            'chart_type': ai_response.get('chart_type'),
            'understanding': {}
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in send_message: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chat_bp.route('/conversations/<int:conversation_id>/title', methods=['PUT'])
@login_required
def update_title(conversation_id):
    """Update conversation title"""
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        data = request.get_json()
        conversation.title = data.get('title')
        db.session.commit()
        
        return jsonify({'success': True, 'conversation': conversation.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/chatbot/status', methods=['GET'])
@login_required
def chatbot_status():
    """Get chatbot status"""
    return jsonify({
        'success': True,
        'status': {
            'model': 'LightweightChatbot',
            'initialized': True,
            'note': 'Using lightweight mode - no memory issues!'
        }
    })
