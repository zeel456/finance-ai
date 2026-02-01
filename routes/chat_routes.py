"""
Chat History Routes
Save as: routes/chat_routes.py
"""

from flask import Blueprint, request, jsonify
from models.database import db
from models.conversation import Conversation
from models.message import Message
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations (list view)"""
    try:
        conversations = Conversation.query.order_by(
            Conversation.updated_at.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with all messages"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict_detailed()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        title = data.get('title', 'New Conversation')
        
        conversation = Conversation(title=title)
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
def add_message(conversation_id):
    """Add a message to a conversation"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        data = request.get_json()
        
        message = Message(
            conversation_id=conversation_id,
            role=data.get('role'),
            content=data.get('content'),
            intent=data.get('intent'),
            confidence=data.get('confidence')
        )
        
        # Set entities if provided
        if data.get('entities'):
            message.set_entities(data.get('entities'))
        
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if not conversation.title or conversation.title == 'New Conversation':
            if message.role == 'user':
                conversation.title = Conversation.generate_title(message.content)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations/<int:conversation_id>/title', methods=['PUT'])
def update_title(conversation_id):
    """Update conversation title"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        data = request.get_json()
        conversation.title = data.get('title')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/conversations/search', methods=['GET'])
def search_conversations():
    """Search conversations by content"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({
                'success': True,
                'conversations': []
            })
        
        # Search in conversation titles and message content
        conversations = Conversation.query.join(Message).filter(
            db.or_(
                Conversation.title.ilike(f'%{query}%'),
                Message.content.ilike(f'%{query}%')
            )
        ).distinct().order_by(Conversation.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500