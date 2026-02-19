"""
Tests for Travel CS AI
"""
import sys
sys.path.insert(0, '../src')

from chat.engine import IntentClassifier, ChatEngine


def test_intent_classifier():
    """测试意图分类"""
    ic = IntentClassifier()
    
    test_cases = [
        ("巴厘岛多少钱？", "price_inquiry"),
        ("推荐个行程", "itinerary_query"),
        ("怎么预订？", "booking"),
        ("我要投诉！", "complaint"),
        ("紧急求助", "emergency"),
    ]
    
    for message, expected_intent in test_cases:
        intent, confidence = ic.classify(message)
        status = "✅" if intent == expected_intent else "❌"
        print(f"{status} '{message}' -> {intent} (confidence: {confidence:.2f})")
    
    print()


def test_chat_engine():
    """测试对话引擎"""
    engine = ChatEngine()
    
    test_messages = [
        "你好",
        "巴厘岛多少钱？",
        "推荐个行程",
        "可以退改吗？",
    ]
    
    session_id = "test_session_001"
    
    for msg in test_messages:
        result = engine.process(session_id, msg)
        print(f"User: {msg}")
        print(f"Bot:  {result['response'][:80]}...")
        print(f"     (intent: {result['intent']}, confidence: {result['confidence']:.2f})")
        print()


def test_kb_search():
    """测试知识库搜索"""
    from chat.engine import SimpleKnowledgeBase
    
    kb = SimpleKnowledgeBase()
    
    print("产品搜索测试:")
    results = kb.search_products("巴厘岛")
    for r in results:
        print(f"  - {r['name']}: ¥{r['price']}")
    
    print("\nFAQ搜索测试:")
    results = kb.search_faqs("预订")
    for r in results:
        print(f"  - Q: {r['question']}")
        print(f"    A: {r['answer'][:50]}...")


if __name__ == "__main__":
    print("🧪 Running Tests\n")
    
    print("=== Intent Classification ===")
    test_intent_classifier()
    
    print("=== Chat Engine ===")
    test_chat_engine()
    
    print("=== Knowledge Base ===")
    test_kb_search()
    
    print("\n✅ All tests completed!")
