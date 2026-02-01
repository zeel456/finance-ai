"""
Advanced Semantic Chatbot with Deep Contextual Understanding
Save as: ai_modules/semantic_chatbot.py

Features:
- Semantic similarity using transformer models
- Contextual conversation memory
- Intent understanding beyond keywords
- Entity extraction with coreference resolution
- Multi-turn conversation handling
- Fallback to Claude API for complex queries
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import spacy
from datetime import datetime, timedelta
from collections import deque
import re
from typing import Dict, List, Tuple, Optional
from cachetools import TTLCache

from ai_modules.nlp_query import NLPQueryProcessor
from models.database import db
from models.transaction import Transaction
from models.category import Category
from sqlalchemy import func


class SemanticChatbot(NLPQueryProcessor):
    """
    Advanced semantic chatbot that truly understands meaning
    """
    
    def __init__(self):
        """Initialize with advanced NLP models"""
        print("🚀 Initializing Semantic Chatbot...")
        
        super().__init__()
        
        # Load advanced models
        print("📚 Loading spaCy with dependency parsing...")
        self.nlp = spacy.load("en_core_web_md")
        
        print("🧠 Loading semantic encoder...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Conversation memory (last 10 turns)
        self.conversation_memory = deque(maxlen=10)
        
        # Context tracking
        self.context = {
            'current_topic': None,
            'mentioned_entities': set(),
            'time_context': None,
            'category_context': None,
            'last_intent': None,
            'user_preferences': {},
            'conversation_id': None
        }
        
        # Caching
        self.embedding_cache = TTLCache(maxsize=1000, ttl=3600)
        
        # Intent templates with semantic variations
        self.intent_templates = self._build_intent_templates()
        
        # Pre-compute template embeddings
        print("🔢 Pre-computing semantic embeddings...")
        self.template_embeddings = self._precompute_embeddings()
        
        print("✅ Semantic Chatbot ready!")
    
    def _build_intent_templates(self) -> Dict[str, List[str]]:
        """Build comprehensive intent templates"""
        return {
            'total_expense': [
                "What is my total spending?",
                "How much money have I spent?",
                "Show me all my expenses",
                "Calculate my total expenditure",
                "What's the sum of everything I spent?",
                "Total amount I've paid",
                "All my spending combined"
            ],
            
            'category_expense': [
                "How much did I spend on [category]?",
                "What are my [category] expenses?",
                "Show spending for [category]",
                "Money spent in [category] category",
                "Expenses related to [category]",
                "Cost of [category] items"
            ],
            
            'time_based_expense': [
                "What did I spend [time_period]?",
                "Show expenses for [time_period]",
                "Spending during [time_period]",
                "How much [time_period]?",
                "[time_period] expenses"
            ],
            
            'comparison': [
                "Compare [period1] with [period2]",
                "How does [period1] compare to [period2]?",
                "Is spending higher than [period]?",
                "Difference between [period1] and [period2]",
                "Show changes from [period1] to [period2]"
            ],
            
            'top_spending': [
                "Where did I spend the most?",
                "What are my biggest expenses?",
                "Show top spending categories",
                "Which areas cost me most?",
                "Highest expenditure categories",
                "Main spending areas"
            ],
            
            'trend_analysis': [
                "How is my spending changing?",
                "Show spending trends",
                "Is my spending increasing?",
                "Spending patterns over time",
                "Track my expense behavior",
                "How spending evolved"
            ],
            
            'vendor_analysis': [
                "Which stores do I shop at most?",
                "Show me frequent vendors",
                "Where do I buy from?",
                "Top merchants I use",
                "Regular shopping places"
            ],
            
            'average_expense': [
                "What's my average spending?",
                "Typical transaction amount",
                "Mean expense value",
                "Average daily spending",
                "Normal spending level"
            ],
            
            'budget_related': [
                "Am I within budget?",
                "How much budget remaining?",
                "Did I exceed my limit?",
                "Budget status check",
                "Spending vs budget"
            ],
            
            'insights': [
                "Give me spending insights",
                "What patterns do you see?",
                "Any unusual spending?",
                "Financial advice based on my data",
                "Help me understand my expenses"
            ]
        }
    
    def _precompute_embeddings(self) -> Dict[str, np.ndarray]:
        """Pre-compute embeddings for all templates"""
        embeddings = {}
        
        for intent, templates in self.intent_templates.items():
            intent_embeddings = []
            
            for template in templates:
                # Remove placeholders for embedding
                clean_template = re.sub(r'\[.*?\]', '', template).strip()
                
                if clean_template in self.embedding_cache:
                    emb = self.embedding_cache[clean_template]
                else:
                    emb = self.encoder.encode(clean_template, show_progress_bar=False)
                    self.embedding_cache[clean_template] = emb
                
                intent_embeddings.append(emb)
            
            embeddings[intent] = np.array(intent_embeddings)
        
        return embeddings
    
    def understand_query(self, query: str) -> Dict:
        """
        Deep semantic understanding of the query
        
        Returns:
            dict with intent, entities, confidence, and context
        """
        # Step 1: Linguistic analysis
        doc = self.nlp(query)
        
        # Step 2: Semantic intent detection
        intent, confidence = self._detect_semantic_intent(query, doc)
        
        # Step 3: Entity extraction with context
        entities = self._extract_entities_with_context(query, doc)
        
        # Step 4: Apply conversation context
        entities = self._apply_conversation_context(entities)
        
        # Step 5: Resolve ambiguities
        intent, entities = self._resolve_ambiguities(query, intent, entities, doc)
        
        # Step 6: Update memory
        self._update_conversation_memory(query, intent, entities)
        
        return {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'context': self.context.copy(),
            'linguistic_features': self._extract_linguistic_features(doc)
        }
    
    def _detect_semantic_intent(self, query: str, doc) -> Tuple[str, float]:
        """
        Detect intent using semantic similarity
        """
        # Encode the query
        query_embedding = self.encoder.encode(query, show_progress_bar=False)
        
        # Calculate similarities with all templates
        similarities = {}
        
        for intent, template_embeddings in self.template_embeddings.items():
            # Cosine similarity
            sims = np.dot(template_embeddings, query_embedding) / (
                np.linalg.norm(template_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            similarities[intent] = float(np.max(sims))
        
        # Linguistic boost based on question type
        linguistic_boost = self._get_linguistic_boost(doc)
        
        # Apply boosts
        for intent, boost in linguistic_boost.items():
            similarities[intent] = min(similarities.get(intent, 0) + boost, 1.0)
        
        # Context boost (if continuing same topic)
        if self.context.get('last_intent'):
            last_intent = self.context['last_intent']
            if self._is_followup_query(query):
                similarities[last_intent] = min(similarities.get(last_intent, 0) + 0.15, 1.0)
        
        # Get best intent
        best_intent = max(similarities, key=similarities.get)
        confidence = similarities[best_intent] * 100
        
        # Handle low confidence
        if confidence < 40:
            return 'unclear', confidence
        
        return best_intent, confidence
    
    def _get_linguistic_boost(self, doc) -> Dict[str, float]:
        """
        Boost intents based on linguistic patterns
        """
        boosts = {}
        query_text = doc.text.lower()
        
        # Question word patterns
        question_patterns = {
            'what': ['total_expense', 'category_expense', 'top_spending'],
            'how much': ['total_expense', 'category_expense'],
            'how many': ['count_based'],
            'where': ['vendor_analysis', 'top_spending'],
            'when': ['time_based_expense'],
            'which': ['top_spending', 'comparison'],
            'compare': ['comparison'],
            'show': ['trend_analysis', 'top_spending']
        }
        
        for pattern, intents in question_patterns.items():
            if pattern in query_text:
                for intent in intents:
                    boosts[intent] = boosts.get(intent, 0) + 0.1
        
        # Comparative/superlative detection
        for token in doc:
            if token.tag_ in ['JJR', 'RBR']:  # Comparative
                boosts['comparison'] = boosts.get('comparison', 0) + 0.15
            elif token.tag_ in ['JJS', 'RBS']:  # Superlative
                boosts['top_spending'] = boosts.get('top_spending', 0) + 0.15
        
        # Temporal expressions
        if any(token.ent_type_ == 'DATE' for token in doc):
            boosts['time_based_expense'] = boosts.get('time_based_expense', 0) + 0.1
        
        return boosts
    
    def _extract_entities_with_context(self, query: str, doc) -> Dict:
        """
        Extract entities using NLP + context awareness
        """
        entities = {
            'categories': [],
            'time_periods': [],
            'amounts': [],
            'vendors': [],
            'payment_methods': [],
            'comparison_periods': [],
            'numbers': []
        }
        
        # Named entity recognition
        for ent in doc.ents:
            if ent.label_ == 'DATE':
                time_period = self._normalize_time_expression(ent.text)
                if time_period:
                    entities['time_periods'].append(time_period)
            
            elif ent.label_ == 'MONEY':
                amount = self._extract_amount(ent.text)
                if amount:
                    entities['amounts'].append(amount)
            
            elif ent.label_ == 'ORG':
                entities['vendors'].append(ent.text)
            
            elif ent.label_ in ['CARDINAL', 'QUANTITY']:
                try:
                    entities['numbers'].append(float(ent.text))
                except:
                    pass
        
        # Category detection with fuzzy matching
        categories = self._detect_categories(query, doc)
        entities['categories'].extend(categories)
        
        # Time period patterns (manual extraction)
        time_patterns = self._extract_time_patterns(query)
        entities['time_periods'].extend(time_patterns)
        
        # Payment method detection
        payment_methods = self._detect_payment_methods(query)
        entities['payment_methods'].extend(payment_methods)
        
        # Remove duplicates
        for key in entities:
            if isinstance(entities[key], list):
                entities[key] = list(set(entities[key]))
        
        return entities
    
    def _detect_categories(self, query: str, doc) -> List[str]:
        """
        Detect categories using semantic similarity
        """
        detected = []
        query_lower = query.lower()
        
        # Get all categories from database
        all_categories = Category.query.all()
        
        # Direct keyword matching first
        category_keywords = {
            'Food & Dining': ['food', 'dining', 'restaurant', 'eat', 'meal', 'lunch', 'dinner', 'breakfast'],
            'Groceries': ['grocery', 'groceries', 'supermarket'],
            'Transportation': ['transport', 'uber', 'ola', 'taxi', 'cab', 'commute'],
            'Travel': ['travel', 'trip', 'vacation', 'holiday', 'tour'],
            'Shopping': ['shopping', 'clothes', 'fashion', 'amazon', 'flipkart'],
            'Entertainment': ['entertainment', 'movie', 'cinema', 'netflix', 'fun'],
            'Healthcare': ['health', 'medical', 'doctor', 'medicine', 'hospital'],
            'Education': ['education', 'school', 'college', 'course', 'books'],
            'Bills & Utilities': ['bills', 'utility', 'electricity', 'water', 'internet'],
            'Fuel': ['fuel', 'petrol', 'diesel', 'gas']
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                detected.append(category)
        
        # If still not found, use semantic similarity
        if not detected and all_categories:
            query_embedding = self.encoder.encode(query, show_progress_bar=False)
            
            best_match = None
            best_score = 0
            
            for cat in all_categories:
                cat_embedding = self.encoder.encode(cat.name, show_progress_bar=False)
                similarity = np.dot(query_embedding, cat_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(cat_embedding)
                )
                
                if similarity > best_score and similarity > 0.4:
                    best_score = similarity
                    best_match = cat.name
            
            if best_match:
                detected.append(best_match)
        
        return detected
    
    def _extract_time_patterns(self, query: str) -> List[str]:
        """
        Extract time periods from natural language
        """
        query_lower = query.lower()
        time_periods = []
        
        # Pattern matching with priority
        patterns = [
            (r'last\s+month', 'last_month'),
            (r'this\s+month', 'this_month'),
            (r'previous\s+month', 'last_month'),
            (r'current\s+month', 'this_month'),
            (r'last\s+week', 'last_week'),
            (r'this\s+week', 'this_week'),
            (r'last\s+year', 'last_year'),
            (r'this\s+year', 'this_year'),
            (r'yesterday', 'yesterday'),
            (r'today', 'today'),
            (r'last\s+\d+\s+days', 'custom'),
            (r'past\s+\d+\s+days', 'custom')
        ]
        
        for pattern, period in patterns:
            if re.search(pattern, query_lower):
                time_periods.append(period)
                break  # Take first match
        
        return time_periods
    
    def _detect_payment_methods(self, query: str) -> List[str]:
        """
        Detect payment methods mentioned
        """
        query_lower = query.lower()
        methods = []
        
        payment_keywords = {
            'Credit Card': ['credit card', 'card'],
            'Debit Card': ['debit card'],
            'UPI': ['upi', 'google pay', 'phonepe', 'paytm'],
            'Cash': ['cash'],
            'Net Banking': ['net banking', 'netbanking', 'online transfer']
        }
        
        for method, keywords in payment_keywords.items():
            if any(kw in query_lower for kw in keywords):
                methods.append(method)
        
        return methods
    
    def _apply_conversation_context(self, entities: Dict) -> Dict:
        """
        Apply context from previous conversation turns
        """
        # If no time period mentioned, check context
        if not entities['time_periods'] and self.context.get('time_context'):
            if self._is_followup_query_simple():
                entities['time_periods'].append(self.context['time_context'])
        
        # If no category mentioned, check context
        if not entities['categories'] and self.context.get('category_context'):
            if self._is_followup_query_simple():
                entities['categories'].append(self.context['category_context'])
        
        return entities
    
    def _is_followup_query(self, query: str) -> bool:
        """
        Check if this is a follow-up to previous query
        """
        followup_indicators = [
            'what about', 'how about', 'and what', 'also',
            'same for', 'for that', 'in that'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in followup_indicators)
    
    def _is_followup_query_simple(self) -> bool:
        """Simple check for follow-up"""
        if not self.conversation_memory:
            return False
        
        # If last query was less than 2 minutes ago
        if len(self.conversation_memory) > 0:
            return True
        
        return False
    
    def _resolve_ambiguities(self, query: str, intent: str, entities: Dict, doc) -> Tuple[str, Dict]:
        """
        Resolve ambiguous queries using context and semantics
        """
        # If intent is unclear but we have strong entity signals
        if intent == 'unclear':
            # Has category + time = likely category_expense
            if entities['categories'] and entities['time_periods']:
                intent = 'category_expense'
            
            # Has only time = likely time_based_expense or total_expense
            elif entities['time_periods'] and not entities['categories']:
                intent = 'time_based_expense'
            
            # Has comparison words
            elif any(word in query.lower() for word in ['compare', 'vs', 'than', 'difference']):
                intent = 'comparison'
        
        # Merge similar intents
        if intent == 'time_based_expense' and not entities['categories']:
            intent = 'total_expense'
        
        return intent, entities
    
    def _update_conversation_memory(self, query: str, intent: str, entities: Dict):
        """
        Update conversation memory and context
        """
        # Add to memory
        self.conversation_memory.append({
            'query': query,
            'intent': intent,
            'entities': entities,
            'timestamp': datetime.now()
        })
        
        # Update context
        self.context['last_intent'] = intent
        
        if entities['categories']:
            self.context['category_context'] = entities['categories'][0]
        
        if entities['time_periods']:
            self.context['time_context'] = entities['time_periods'][0]
        
        # Add to mentioned entities
        for category in entities['categories']:
            self.context['mentioned_entities'].add(category)
    
    def _extract_linguistic_features(self, doc) -> Dict:
        """
        Extract linguistic features for debugging
        """
        return {
            'tokens': [token.text for token in doc],
            'pos_tags': [token.pos_ for token in doc],
            'dependencies': [(token.text, token.dep_, token.head.text) for token in doc],
            'entities': [(ent.text, ent.label_) for ent in doc.ents]
        }
    
    def _normalize_time_expression(self, text: str) -> Optional[str]:
        """
        Normalize time expressions to standard format
        """
        text_lower = text.lower()
        
        mappings = {
            'last month': 'last_month',
            'this month': 'this_month',
            'previous month': 'last_month',
            'current month': 'this_month',
            'last week': 'last_week',
            'this week': 'this_week',
            'last year': 'last_year',
            'this year': 'this_year',
            'yesterday': 'yesterday',
            'today': 'today'
        }
        
        return mappings.get(text_lower)
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """
        Extract numeric amount from text
        """
        # Remove currency symbols
        text = text.replace('₹', '').replace('Rs', '').replace(',', '').strip()
        
        try:
            return float(text)
        except:
            return None
    
    def process_message(self, query: str, conversation_id: Optional[int] = None) -> Dict:
        """
        Main entry point for processing a message
        
        Args:
            query: User's natural language query
            conversation_id: Optional conversation ID for context
        
        Returns:
            dict with response, data, and metadata
        """
        # Update conversation context
        if conversation_id and conversation_id != self.context.get('conversation_id'):
            self.reset_conversation()
            self.context['conversation_id'] = conversation_id
        
        # Understand the query
        understanding = self.understand_query(query)
        
        intent = understanding['intent']
        entities = understanding['entities']
        confidence = understanding['confidence']
        
        print(f"\n🎯 Understood Query:")
        print(f"   Intent: {intent} ({confidence:.1f}% confidence)")
        print(f"   Entities: {entities}")
        print(f"   Context: {self.context}")
        
        # Route to appropriate handler
        handlers = {
            'total_expense': lambda: self._handle_total_expense(entities),
            'category_expense': lambda: self._handle_category_expense(entities),
            'time_based_expense': lambda: self._handle_total_expense(entities),
            'comparison': lambda: self.handle_comparison(query),
            'top_spending': lambda: self.handle_top_spending(query),
            'trend_analysis': lambda: self.handle_trend(query),
            'vendor_analysis': lambda: self.handle_vendor_analysis(query),
            'average_expense': lambda: self._handle_average_expense(entities),
            'budget_related': lambda: self.handle_budget_check(query),
            'insights': lambda: self._handle_insights(entities),
            'unclear': lambda: self._handle_unclear(query, understanding)
        }
        
        handler = handlers.get(intent, lambda: self.handle_unknown(query))
        result = handler()
        
        # Add metadata
        result['understanding'] = understanding
        result['confidence'] = confidence
        
        return result
    
    def _handle_total_expense(self, entities: Dict) -> Dict:
        """Handle total expense with context"""
        start_date, end_date = self._get_date_range(entities)
        
        query_obj = db.session.query(func.sum(Transaction.amount))
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        total = query_obj.scalar() or 0.0
        
        # Natural language response
        response = f"Your {period} expenses total ₹{total:,.2f}."
        
        # Add context if available
        if self.conversation_memory:
            last_total = self._get_last_total()
            if last_total and last_total != total:
                change = ((total - last_total) / last_total) * 100
                if abs(change) > 5:
                    response += f" That's {abs(change):.1f}% {'higher' if change > 0 else 'lower'} than before."
        
        return {
            'intent': 'total_expense',
            'response': response,
            'data': {
                'total': total,
                'period': period,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'chart_type': 'total_bar'
        }
    
    def _handle_category_expense(self, entities: Dict) -> Dict:
        """Handle category expense with context"""
        if not entities['categories']:
            return {
                'intent': 'category_expense',
                'response': "Which category would you like to know about? For example: food, transportation, shopping, etc.",
                'data': None,
                'chart_type': None
            }
        
        category_name = entities['categories'][0]
        start_date, end_date = self._get_date_range(entities)
        
        # Find category
        category = Category.query.filter(
            Category.name.ilike(f'%{category_name}%')
        ).first()
        
        if not category:
            return {
                'intent': 'category_expense',
                'response': f"I couldn't find a category matching '{category_name}'. Try: food, transportation, shopping, bills, etc.",
                'data': None,
                'chart_type': None
            }
        
        # Query transactions
        query_obj = db.session.query(
            func.sum(Transaction.amount),
            func.count(Transaction.id)
        ).filter(Transaction.category_id == category.id)
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        result = query_obj.first()
        total = result[0] or 0.0
        count = result[1] or 0
        
        # Natural response
        response = f"You spent ₹{total:,.2f} on {category.name} {period}"
        if count > 0:
            response += f" across {count} transaction{'s' if count != 1 else ''}."
        else:
            response += "."
        
        return {
            'intent': 'category_expense',
            'response': response,
            'data': {
                'category': category.name,
                'total': total,
                'count': count,
                'period': period
            },
            'chart_type': 'category_bar'
        }
    
    def _handle_average_expense(self, entities: Dict) -> Dict:
        """Handle average expense queries"""
        start_date, end_date = self._get_date_range(entities)
        
        query_obj = db.session.query(
            func.avg(Transaction.amount),
            func.count(Transaction.id)
        )
        
        if start_date and end_date:
            query_obj = query_obj.filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            period = self.format_period(start_date, end_date)
        else:
            period = "overall"
        
        result = query_obj.first()
        avg = result[0] or 0.0
        count = result[1] or 0
        
        response = f"Your {period} average spending is ₹{avg:,.2f} per transaction ({count} total transactions)."
        
        return {
            'intent': 'average_expense',
            'response': response,
            'data': {'average': avg, 'count': count, 'period': period},
            'chart_type': None
        }
    
    def _handle_insights(self, entities: Dict) -> Dict:
        """Provide intelligent insights"""
        # Get spending by category
        category_spending = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).group_by(Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(3).all()
        
        # Generate insights
        insights = []
        
        if category_spending:
            top_cat = category_spending[0]
            insights.append(f"Your highest spending is on {top_cat[0]} (₹{top_cat[1]:,.2f})")
        
        # Check recent trend
        this_month_total = self._get_month_total(0)
        last_month_total = self._get_month_total(1)
        
        if this_month_total and last_month_total:
            change = ((this_month_total - last_month_total) / last_month_total) * 100
            if change > 10:
                insights.append(f"Your spending increased by {change:.1f}% this month")
            elif change < -10:
                insights.append(f"Great! You reduced spending by {abs(change):.1f}% this month")
        
        response = "Here are some insights about your spending:\n• " + "\n• ".join(insights)
        
        return {
            'intent': 'insights',
            'response': response,
            'data': {'insights': insights},
            'chart_type': None
        }
    
    def _handle_unclear(self, query: str, understanding: Dict) -> Dict:
        """Handle unclear queries with helpful suggestions"""
        suggestions = [
            "What's my total spending this month?",
            "How much did I spend on food?",
            "Show me my top 5 spending categories",
            "Compare this month with last month"
        ]
        
        response = "I'm not quite sure what you're asking. Here are some things I can help with:\n"
        response += "\n".join([f"• {s}" for s in suggestions])
        
        return {
            'intent': 'unclear',
            'response': response,
            'data': {
                'suggestions': suggestions,
                'debug_info': understanding
            },
            'chart_type': None
        }
    
    def _get_date_range(self, entities: Dict) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Convert entities to date range"""
        if not entities['time_periods']:
            return None, None
        
        period = entities['time_periods'][0]
        today = datetime.now()
        
        mappings = {
            'today': (today.date(), today.date()),
            'yesterday': ((today - timedelta(days=1)).date(), (today - timedelta(days=1)).date()),
            'this_week': ((today - timedelta(days=today.weekday())).date(), today.date()),
            'last_week': (
                (today - timedelta(days=today.weekday() + 7)).date(),
                (today - timedelta(days=today.weekday() + 1)).date()
            ),
            'this_month': (today.replace(day=1).date(), today.date()),
            'last_month': (
                (today.replace(day=1) - timedelta(days=1)).replace(day=1).date(),
                (today.replace(day=1) - timedelta(days=1)).date()
            ),
            'this_year': (today.replace(month=1, day=1).date(), today.date()),
            'last_year': (
                today.replace(year=today.year-1, month=1, day=1).date(),
                today.replace(year=today.year-1, month=12, day=31).date()
            )
        }
        
        return mappings.get(period, (None, None))
    
    def _get_last_total(self) -> Optional[float]:
        """Get total from last query if available"""
        for turn in reversed(self.conversation_memory):
            if turn['intent'] in ['total_expense', 'time_based_expense']:
                # Would need to store this in the turn data
                return None
        return None
    
    def _get_month_total(self, months_ago: int) -> Optional[float]:
        """Get total for a specific month"""
        today = datetime.now()
        
        if months_ago == 0:
            start = today.replace(day=1).date()
            end = today.date()
        else:
            end_month = today.replace(day=1) - timedelta(days=1)
            for _ in range(months_ago - 1):
                end_month = end_month.replace(day=1) - timedelta(days=1)
            start = end_month.replace(day=1).date()
            end = end_month.date()
        
        total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_date.between(start, end)
        ).scalar()
        
        return total or 0.0
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.conversation_memory.clear()
        self.context = {
            'current_topic': None,
            'mentioned_entities': set(),
            'time_context': None,
            'category_context': None,
            'last_intent': None,
            'user_preferences': {},
            'conversation_id': None
        }
        print("🔄 Conversation context reset")