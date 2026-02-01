from app import app

"""
Side-by-Side Comparison: Old vs New Chatbot
Save as: comparison_example.py

This demonstrates the difference between keyword-based and semantic understanding
"""

from ai_modules.nlp_query import NLPQueryProcessor  # Old system
from ai_modules.semantic_chatbot import SemanticChatbot  # New system


def compare_systems():
    """Compare old keyword-based vs new semantic system"""
    
    print("=" * 100)
    print(" " * 35 + "CHATBOT COMPARISON")
    print("=" * 100)
    print("\n")
    
    # Initialize both systems
    old_bot = NLPQueryProcessor()
    new_bot = SemanticChatbot()
    
    # Test cases with varying naturalness
    test_cases = [
        {
            'query': "What's my total spending?",
            'difficulty': 'EASY',
            'description': 'Standard query with clear keywords'
        },
        {
            'query': "How much money have I spent?",
            'difficulty': 'EASY',
            'description': 'Natural variation without keyword "total"'
        },
        {
            'query': "Show me everything I paid for",
            'difficulty': 'MEDIUM',
            'description': 'Very natural phrasing, no typical keywords'
        },
        {
            'query': "I want to see where my money went",
            'difficulty': 'MEDIUM',
            'description': 'Conversational request'
        },
        {
            'query': "What did dining cost me?",
            'difficulty': 'MEDIUM',
            'description': 'Category query with synonym'
        },
        {
            'query': "How much went to restaurants?",
            'difficulty': 'MEDIUM',
            'description': 'Category query without explicit category keyword'
        },
        {
            'query': "What about transportation?",
            'difficulty': 'HARD',
            'description': 'Follow-up query (context-dependent)'
        },
        {
            'query': "Is my spending going up?",
            'difficulty': 'HARD',
            'description': 'Implicit comparison query'
        },
        {
            'query': "Help me understand my expenses",
            'difficulty': 'HARD',
            'description': 'Open-ended, abstract request'
        },
        {
            'query': "Where am I bleeding money?",
            'difficulty': 'VERY HARD',
            'description': 'Metaphorical language'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 100}")
        print(f"TEST CASE {i}: {test['description']}")
        print(f"Difficulty: {test['difficulty']}")
        print(f"{'─' * 100}")
        print(f"\n📝 Query: \"{test['query']}\"")
        print()
        
        # OLD SYSTEM
        print(f"{'🔴 OLD SYSTEM (Keyword-based)':<50}")
        print("─" * 50)
        try:
            old_intent = old_bot.detect_intent(test['query'])
            print(f"  Intent Detected: {old_intent}")
            
            if old_intent == 'unknown':
                print(f"  ❌ Failed to understand")
            else:
                print(f"  ⚠️  Basic keyword match")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
        
        # NEW SYSTEM
        print(f"{'🟢 NEW SYSTEM (Semantic)':<50}")
        print("─" * 50)
        try:
            understanding = new_bot.understand_query(test['query'])
            print(f"  Intent: {understanding['intent']}")
            print(f"  Confidence: {understanding['confidence']:.1f}%")
            
            if understanding['entities']['categories']:
                print(f"  Categories: {understanding['entities']['categories']}")
            if understanding['entities']['time_periods']:
                print(f"  Time Periods: {understanding['entities']['time_periods']}")
            
            if understanding['confidence'] >= 70:
                print(f"  ✅ High confidence understanding")
            elif understanding['confidence'] >= 50:
                print(f"  ⚠️  Moderate confidence")
            else:
                print(f"  ❌ Low confidence")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
        
        # Reset new bot context for next test
        new_bot.reset_conversation()
    
    print(f"\n{'=' * 100}\n")


def demonstrate_context_awareness():
    """Show context handling in conversation"""
    
    print("=" * 100)
    print(" " * 30 + "CONTEXT AWARENESS DEMONSTRATION")
    print("=" * 100)
    print("\n")
    
    old_bot = NLPQueryProcessor()
    new_bot = SemanticChatbot()
    
    conversation = [
        "How much did I spend on food this month?",
        "What about transportation?",  # Should inherit "this month"
        "And last month?",  # Should inherit "transportation"
    ]
    
    print("CONVERSATION FLOW:")
    print("─" * 100)
    
    for i, query in enumerate(conversation, 1):
        print(f"\n🗣️  Turn {i}: \"{query}\"")
        print()
        
        # OLD SYSTEM
        print("  🔴 OLD SYSTEM:")
        old_intent = old_bot.detect_intent(query)
        old_category = old_bot.extract_category(query)
        old_dates = old_bot.extract_date_range(query)
        
        print(f"     Intent: {old_intent}")
        print(f"     Category: {old_category or 'None detected'}")
        print(f"     Time: {old_dates if old_dates != (None, None) else 'None detected'}")
        
        if i > 1:
            if not old_category:
                print(f"     ❌ Lost category context from previous turn")
            if old_dates == (None, None):
                print(f"     ❌ Lost time context from previous turn")
        
        print()
        
        # NEW SYSTEM
        print("  🟢 NEW SYSTEM:")
        understanding = new_bot.understand_query(query)
        
        print(f"     Intent: {understanding['intent']} ({understanding['confidence']:.1f}%)")
        print(f"     Categories: {understanding['entities']['categories'] or 'None in query'}")
        print(f"     Time: {understanding['entities']['time_periods'] or 'None in query'}")
        
        if i > 1:
            context = understanding['context']
            if context.get('category_context'):
                print(f"     ✅ Using category from context: {context['category_context']}")
            if context.get('time_context'):
                print(f"     ✅ Using time from context: {context['time_context']}")
        
        print()
    
    print(f"{'=' * 100}\n")


def show_semantic_similarity():
    """Demonstrate semantic similarity understanding"""
    
    print("=" * 100)
    print(" " * 30 + "SEMANTIC SIMILARITY EXAMPLES")
    print("=" * 100)
    print("\n")
    
    new_bot = SemanticChatbot()
    
    # Groups of semantically similar queries
    similar_groups = [
        {
            'meaning': 'Total Spending',
            'queries': [
                "What's my total expense?",
                "How much money did I spend?",
                "Show me all my spending",
                "Calculate everything I paid for",
                "What's the sum of my expenses?",
            ]
        },
        {
            'meaning': 'Food Category',
            'queries': [
                "How much on food?",
                "What did dining cost?",
                "Show restaurant expenses",
                "Money spent eating out",
                "What did I spend on meals?",
            ]
        },
        {
            'meaning': 'Top Spending',
            'queries': [
                "Where do I spend most?",
                "What are my biggest expenses?",
                "Which categories cost most?",
                "Show me my highest spending areas",
                "Where does my money go?",
            ]
        }
    ]
    
    for group in similar_groups:
        print(f"\n{'─' * 100}")
        print(f"MEANING: {group['meaning']}")
        print(f"{'─' * 100}\n")
        
        for query in group['queries']:
            understanding = new_bot.understand_query(query)
            
            confidence_emoji = "✅" if understanding['confidence'] >= 80 else "⚠️" if understanding['confidence'] >= 60 else "❌"
            
            print(f"{confidence_emoji} \"{query}\"")
            print(f"   → {understanding['intent']} ({understanding['confidence']:.1f}%)")
        
        # Reset for next group
        new_bot.reset_conversation()
    
    print(f"\n{'=' * 100}\n")


def main():
    """Run all comparisons"""
    
    print("\n" + "🤖" * 50)
    print(" " * 40 + "COMPREHENSIVE COMPARISON")
    print("🤖" * 50 + "\n")
    
    print("This comparison demonstrates:")
    print("1. How the new system understands natural language variations")
    print("2. Context awareness in multi-turn conversations")
    print("3. Semantic similarity recognition")
    print("\n")
    
    input("Press Enter to start comparison...")
    
    # Comparison 1: Basic understanding
    compare_systems()
    
    input("\nPress Enter for context awareness demo...")
    
    # Comparison 2: Context handling
    demonstrate_context_awareness()
    
    input("\nPress Enter for semantic similarity demo...")
    
    # Comparison 3: Semantic similarity
    show_semantic_similarity()
    
    print("\n" + "✅" * 50)
    print(" " * 35 + "COMPARISON COMPLETE")
    print("✅" * 50 + "\n")
    
    print("\nKEY TAKEAWAYS:")
    print("─" * 100)
    print("🔴 OLD SYSTEM:")
    print("   • Relies on exact keyword matching")
    print("   • Fails with natural variations")
    print("   • No context awareness")
    print("   • Limited to predefined patterns")
    print()
    print("🟢 NEW SYSTEM:")
    print("   • Understands semantic meaning")
    print("   • Handles natural language variations")
    print("   • Maintains conversation context")
    print("   • Resolves ambiguities intelligently")
    print("   • Provides confidence scores")
    print("─" * 100 + "\n")


if __name__ == "__main__":
    with app.app_context():
        main()
