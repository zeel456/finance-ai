from app import app

"""
Test Script for Semantic Chatbot
Save as: test_semantic_chatbot.py

Run this to see how the semantic chatbot understands queries
"""

from ai_modules.semantic_chatbot import SemanticChatbot
from datetime import datetime


def test_semantic_understanding():
    """Test various query patterns"""
    
    print("=" * 80)
    print("SEMANTIC CHATBOT TEST")
    print("=" * 80)
    
    # Initialize chatbot
    bot = SemanticChatbot()
    
    # Test queries showing semantic understanding
    test_queries = [
        # Natural variations of "total spending"
        ("What's my total spending?", "Direct total expense query"),
        ("How much money have I spent?", "Alternative phrasing"),
        ("Calculate all my expenses", "Command form"),
        ("Show me everything I've paid for", "Very natural phrasing"),
        
        # Category queries with different phrasings
        ("How much did I spend on food?", "Category expense - direct"),
        ("What are my dining expenses?", "Category expense - synonym"),
        ("Money spent eating out", "Category expense - informal"),
        ("Show me restaurant costs", "Category expense - specific vendor type"),
        
        # Time-based queries
        ("What did I spend last month?", "Time-based"),
        ("How much this week?", "Short time query"),
        ("Expenses in January", "Specific month"),
        
        # Comparison queries
        ("Compare this month with last month", "Explicit comparison"),
        ("Is my spending higher than before?", "Implicit comparison"),
        ("How does this month look vs last?", "Casual comparison"),
        
        # Follow-up queries (context-dependent)
        ("What about transportation?", "Follow-up category switch"),
        ("And what about last month?", "Follow-up time switch"),
        ("How about shopping?", "Follow-up variation"),
        
        # Average/insights
        ("What's my average spending?", "Average query"),
        ("Give me some insights", "Open-ended insights"),
        ("Where am I spending the most?", "Top spending - natural"),
        ("Which categories cost me most?", "Top spending - alternative"),
        
        # Complex semantic queries
        ("I want to understand my spending patterns", "Very natural request"),
        ("Help me see where my money goes", "Conversational"),
        ("Show me my financial behavior", "Abstract concept"),
        
        # Ambiguous queries (should handle gracefully)
        ("How much?", "Very vague"),
        ("What about food?", "Depends on context"),
    ]
    
    for i, (query, description) in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {description}")
        print(f"Query: \"{query}\"")
        print(f"{'-' * 80}")
        
        # Get understanding
        understanding = bot.understand_query(query)
        
        print(f"✓ Intent: {understanding['intent']}")
        print(f"✓ Confidence: {understanding['confidence']:.1f}%")
        print(f"✓ Entities:")
        for entity_type, values in understanding['entities'].items():
            if values:
                print(f"   - {entity_type}: {values}")
        
        print(f"\n✓ Context Applied:")
        context = understanding['context']
        if context.get('category_context'):
            print(f"   - Category context: {context['category_context']}")
        if context.get('time_context'):
            print(f"   - Time context: {context['time_context']}")
        if context.get('last_intent'):
            print(f"   - Last intent: {context['last_intent']}")
    
    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print(f"{'=' * 80}\n")


def test_conversation_flow():
    """Test a multi-turn conversation"""
    
    print("\n" + "=" * 80)
    print("CONVERSATION FLOW TEST")
    print("=" * 80 + "\n")
    
    bot = SemanticChatbot()
    
    conversation = [
        "What's my total spending this month?",
        "How much did I spend on food?",
        "What about transportation?",  # Context: should inherit time period
        "And last month?",  # Context: should inherit category (transportation)
        "Compare this month with last month",
        "Show me my top spending categories",
        "What's my average transaction amount?",
    ]
    
    for i, query in enumerate(conversation, 1):
        print(f"\n🗣️  USER (Turn {i}): {query}")
        
        understanding = bot.understand_query(query)
        
        print(f"🤖 BOT Understanding:")
        print(f"   Intent: {understanding['intent']} ({understanding['confidence']:.1f}%)")
        print(f"   Entities: {understanding['entities']}")
        print(f"   Context Memory: {len(bot.conversation_memory)} turns")
        
        # Show context inheritance
        if i > 1:
            print(f"   📝 Context:")
            if understanding['context'].get('category_context'):
                print(f"      - Using category: {understanding['context']['category_context']}")
            if understanding['context'].get('time_context'):
                print(f"      - Using time: {understanding['context']['time_context']}")
    
    print(f"\n{'=' * 80}\n")


def test_semantic_similarity():
    """Test semantic similarity matching"""
    
    print("\n" + "=" * 80)
    print("SEMANTIC SIMILARITY TEST")
    print("=" * 80 + "\n")
    
    bot = SemanticChatbot()
    
    # Pairs of semantically similar queries
    similar_pairs = [
        ("What's my total expense?", "How much money did I spend?"),
        ("Show food spending", "What did I spend on dining?"),
        ("Compare months", "Show me month over month changes"),
        ("Where do I spend most?", "What are my biggest expenses?"),
    ]
    
    for query1, query2 in similar_pairs:
        print(f"\nQuery 1: \"{query1}\"")
        u1 = bot.understand_query(query1)
        print(f"  → Intent: {u1['intent']} ({u1['confidence']:.1f}%)")
        
        # Reset to avoid context effects
        bot.reset_conversation()
        
        print(f"\nQuery 2: \"{query2}\"")
        u2 = bot.understand_query(query2)
        print(f"  → Intent: {u2['intent']} ({u2['confidence']:.1f}%)")
        
        if u1['intent'] == u2['intent']:
            print(f"  ✅ MATCH: Both queries understood as '{u1['intent']}'")
        else:
            print(f"  ❌ DIFFERENT: '{u1['intent']}' vs '{u2['intent']}'")
        
        print("-" * 80)
    
    print()


def main():
    """Run all tests"""
    
    print("\n" + "🤖" * 40)
    print("SEMANTIC CHATBOT COMPREHENSIVE TEST SUITE")
    print("🤖" * 40 + "\n")
    
    try:
        # Test 1: Query understanding
        test_semantic_understanding()
        
        # Test 2: Conversation flow
        test_conversation_flow()
        
        # Test 3: Semantic similarity
        test_semantic_similarity()
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    with app.app_context():
        main()
