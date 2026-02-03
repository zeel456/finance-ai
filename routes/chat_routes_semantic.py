"""
Chat Routes - DROP-IN REPLACEMENT
Save as: routes/chat_routes_semantic.py

✅ Works with your existing semantic_chatbot.py
✅ All fixes included
✅ Just replace and deploy
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.conversation import Conversation
from models.message import Message
from datetime import datetime
import gc

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Initialize chatbot lazily
_semantic_bot = None

def get_semantic_bot():
    """Get or create semantic chatbot instance (lazy initialization)"""
    global _semantic_bot
    if _semantic_bot is None:
        print("🚀 Initializing Semantic Chatbot (first use)...", flush=True)
        try:
            # ✅ Import here to avoid loading at startup
            from ai_modules.semantic_chatbot import SemanticChatbot
            _semantic_bot = SemanticChatbot()
            print("✅ Semantic Chatbot initialized successfully", flush=True)
            # ✅ Force garbage collection after init
            gc.collect()
        except Exception as e:
            import traceback
            print(f"❌ Failed to initialize SemanticChatbot: {e}", flush=True)
            print(traceback.format_exc(), flush=True)
            _semantic_bot = None
            raise RuntimeError(
                f"Chatbot initialization failed: {e}. "
                "Check that spaCy model (en_core_web_md) and "
                "sentence-transformers are installed correctly."
            )
    return _semantic_bot


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
    """Get a specific conversation with all messages"""
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
    Send a message and get AI response
    ✅ ALL FIXES APPLIED
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
            return jsonify({'success': False, 'error': 'Message content cannot be empty'}), 400
        
        print(f"💬 User {current_user.id}: {user_message_content[:50]}...", flush=True)
        
        # 1. Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role='user',
            content=user_message_content
        )
        db.session.add(user_message)
        db.session.flush()
        
        # 2. Process with semantic chatbot
        try:
            bot = get_semantic_bot()
            
            # ✅ Check if bot has process_message with user_id parameter
            import inspect
            sig = inspect.signature(bot.process_message)
            
            if 'user_id' in sig.parameters:
                # New version with user_id
                ai_response = bot.process_message(
                    query=user_message_content,
                    conversation_id=conversation_id,
                    user_id=current_user.id
                )
            else:
                # Old version without user_id - set it manually
                bot.current_user_id = current_user.id
                ai_response = bot.process_message(
                    query=user_message_content,
                    conversation_id=conversation_id
                )
            
            # 3. Save AI response message
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_response['response'],
                intent=ai_response.get('intent'),
                confidence=ai_response.get('confidence')
            )
            
            if ai_response.get('understanding', {}).get('entities'):
                assistant_message.set_entities(ai_response['understanding']['entities'])
            
            db.session.add(assistant_message)
            
        except RuntimeError as e:
            # Chatbot init failure
            print(f"❌ RuntimeError: {str(e)}", flush=True)
            
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=(
                    "I'm having trouble initializing my AI models right now. "
                    "This usually happens when the server is starting up or under heavy load. "
                    "Please wait a moment and try again."
                )
            )
            db.session.add(assistant_message)
            ai_response = {
                'response': assistant_message.content,
                'intent': 'error',
                'data': None,
                'chart_type': None,
                'understanding': {'error': str(e)}
            }
        
        # 4. Update conversation
        conversation.updated_at = datetime.utcnow()
        
        if not conversation.title or conversation.title == 'New Conversation':
            conversation.title = user_message_content[:50] + ('...' if len(user_message_content) > 50 else '')
        
        # 5. Commit all changes
        db.session.commit()
        
        # 6. ✅ FIX: Convert sets to lists for JSON serialization
        understanding = ai_response.get('understanding', {})
        if understanding and 'context' in understanding:
            context = understanding['context']
            if 'mentioned_entities' in context and isinstance(context['mentioned_entities'], set):
                context['mentioned_entities'] = list(context['mentioned_entities'])
        
        print(f"✅ Response generated successfully", flush=True)
        
        # ✅ Cleanup memory
        gc.collect()
        
        # 7. Return response
        return jsonify({
            'success': True,
            'user_message': user_message.to_dict(),
            'assistant_message': assistant_message.to_dict(),
            'data': ai_response.get('data'),
            'chart_type': ai_response.get('chart_type'),
            'understanding': understanding
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


@chat_bp.route('/conversations/search', methods=['GET'])
@login_required
def search_conversations():
    """Search conversations by content"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'success': True, 'conversations': []})
        
        conversations = Conversation.query.filter_by(
            user_id=current_user.id
        ).join(Message).filter(
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
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/conversations/<int:conversation_id>/context/reset', methods=['POST'])
@login_required
def reset_context(conversation_id):
    """Reset the chatbot context for this conversation"""
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        global _semantic_bot
        if _semantic_bot is not None:
            _semantic_bot.reset_conversation()
        
        return jsonify({'success': True, 'message': 'Context reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/chatbot/status', methods=['GET'])
@login_required
def chatbot_status():
    """Get current chatbot status and context"""
    try:
        global _semantic_bot
        
        if _semantic_bot is None:
            return jsonify({
                'success': True,
                'status': {
                    'model': 'SemanticChatbot',
                    'initialized': False,
                    'note': 'Bot will initialize on first message'
                }
            })
        
        bot = _semantic_bot
        
        # Convert context for JSON serialization
        context_json = {}
        for k, v in bot.context.items():
            if isinstance(v, set):
                context_json[k] = list(v)
            elif isinstance(v, (dict, list, int, float, bool, type(None), str)):
                context_json[k] = v
            else:
                context_json[k] = str(v)
        
        return jsonify({
            'success': True,
            'status': {
                'model': 'SemanticChatbot',
                'initialized': True,
                'context': context_json,
                'memory_size': len(bot.conversation_memory),
                'cache_size': len(bot.embedding_cache) if hasattr(bot, 'embedding_cache') else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
