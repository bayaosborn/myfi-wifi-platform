"""
Intent Classification Tests
app/tests/test_intent.py

Test suite for intent classifier
Run: python -m pytest app/tests/test_intent.py -v
"""

import pytest
from app.logic.core.intent import IntentClassifier


@pytest.fixture
def classifier():
    """Create intent classifier instance"""
    return IntentClassifier()


class TestContactIntents:
    """Test contact-related intent classification"""
    
    def test_call_action(self, classifier):
        """Test call intent detection"""
        messages = [
            "call John",
            "ring Sarah",
            "phone Mike",
            "give John a call"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'contact_action', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_message_action(self, classifier):
        """Test message intent detection"""
        messages = [
            "text Sarah",
            "send a message to John",
            "message Mike",
            "SMS John"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'contact_action', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_add_contact(self, classifier):
        """Test add contact intent"""
        messages = [
            "add contact John 0712345678",
            "save this number",
            "create new contact"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'contact_management', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


class TestMerchantIntents:
    """Test merchant-related intent classification"""
    
    def test_merchant_search(self, classifier):
        """Test merchant search intent"""
        messages = [
            "I want boots",
            "find gas",
            "where can I buy soap",
            "looking for shoes",
            "I need cleaning supplies"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'merchant_search', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_product_browse(self, classifier):
        """Test product browsing intent"""
        messages = [
            "what does Mbauda sell",
            "show me Viva Ronaldo's products",
            "what's available at Mbauda Chemicals"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'product_browse', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_order_request(self, classifier):
        """Test order intent"""
        messages = [
            "order 6kg gas",
            "buy CR7 boots",
            "I'll take 2 soaps",
            "purchase the boots",
            "kununua sabuni"  # Swahili: buy soap
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'order_request', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


class TestDisambiguation:
    """Test disambiguation of ambiguous messages"""
    
    def test_want_disambiguation(self, classifier):
        """Test 'want' disambiguation"""
        test_cases = [
            ("I want to call John", 'contact_action'),
            ("I want boots", 'merchant_search'),
            ("I want to order gas", 'order_request')
        ]
        
        for msg, expected_intent in test_cases:
            result = classifier.classify(msg)
            assert result['intent'] == expected_intent, f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_context_sensitive(self, classifier):
        """Test context-sensitive classification"""
        test_cases = [
            ("call John about boots", 'contact_action'),  # Contact action, not merchant
            ("text Sarah about the gas order", 'contact_action'),  # Contact action
            ("find boots to buy", 'merchant_search')  # Merchant search
        ]
        
        for msg, expected_intent in test_cases:
            result = classifier.classify(msg)
            assert result['intent'] == expected_intent, f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


class TestRecallIntents:
    """Test recall query classification"""
    
    def test_recall_queries(self, classifier):
        """Test recall intent detection"""
        messages = [
            "you showed me boots",
            "I ordered from Mbauda",
            "what did I buy last week",
            "you told me about gas cylinders",
            "I remember you mentioned soap"
        ]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'recall_query', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


class TestSwahiliSheng:
    """Test Swahili/Sheng support"""
    
    def test_swahili_intents(self, classifier):
        """Test Swahili intent detection"""
        test_cases = [
            ("nataka viatu", 'merchant_search'),  # I want shoes
            ("nipigie John", 'contact_action'),  # Call John
            ("kununua sabuni", 'order_request'),  # Buy soap
            ("nataka gesi", 'merchant_search')  # I want gas
        ]
        
        for msg, expected_intent in test_cases:
            result = classifier.classify(msg)
            assert result['intent'] == expected_intent, f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


class TestEntityExtraction:
    """Test entity extraction from messages"""
    
    def test_product_extraction(self, classifier):
        """Test product entity extraction"""
        result = classifier.classify("I want CR7 boots")
        
        assert result['intent'] == 'merchant_search'
        assert result['entities'].get('product') is not None
        print(f"✅ Extracted product: {result['entities'].get('product')}")
    
    def test_contact_extraction(self, classifier):
        """Test contact name extraction"""
        result = classifier.classify("call John")
        
        assert result['intent'] == 'contact_action'
        assert result['entities'].get('contact_name') is not None
        print(f"✅ Extracted contact: {result['entities'].get('contact_name')}")
    
    def test_quantity_extraction(self, classifier):
        """Test quantity extraction"""
        result = classifier.classify("order 2 soaps")
        
        assert result['intent'] == 'order_request'
        assert result['entities'].get('quantity') is not None
        print(f"✅ Extracted quantity: {result['entities'].get('quantity')}")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_message(self, classifier):
        """Test empty message handling"""
        result = classifier.classify("")
        
        # Should default to general_chat
        assert result['intent'] == 'general_chat'
        print(f"✅ Empty message → {result['intent']}")
    
    def test_greeting(self, classifier):
        """Test greeting classification"""
        messages = ["hello", "hi", "hey", "good morning"]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'general_chat', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")
    
    def test_thank_you(self, classifier):
        """Test thank you classification"""
        messages = ["thanks", "thank you", "appreciate it"]
        
        for msg in messages:
            result = classifier.classify(msg)
            assert result['intent'] == 'general_chat', f"Failed for: {msg}"
            print(f"✅ {msg} → {result['intent']}")


# Run tests with detailed output
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    print("\n" + "="*50)
    print("INTENT CLASSIFICATION TEST SUITE")
    print("="*50 + "\n")
    
    # Test contact intents
    print("📞 Testing Contact Intents...")
    test_contact = TestContactIntents()
    test_contact.test_call_action(classifier)
    test_contact.test_message_action(classifier)
    test_contact.test_add_contact(classifier)
    
    # Test merchant intents
    print("\n🛒 Testing Merchant Intents...")
    test_merchant = TestMerchantIntents()
    test_merchant.test_merchant_search(classifier)
    test_merchant.test_product_browse(classifier)
    test_merchant.test_order_request(classifier)
    
    # Test disambiguation
    print("\n🎯 Testing Disambiguation...")
    test_disamb = TestDisambiguation()
    test_disamb.test_want_disambiguation(classifier)
    test_disamb.test_context_sensitive(classifier)
    
    # Test recall
    print("\n🧠 Testing Recall Intents...")
    test_recall = TestRecallIntents()
    test_recall.test_recall_queries(classifier)
    
    # Test Swahili
    print("\n🇰🇪 Testing Swahili/Sheng...")
    test_swahili = TestSwahiliSheng()
    test_swahili.test_swahili_intents(classifier)
    
    # Test entity extraction
    print("\n📦 Testing Entity Extraction...")
    test_entities = TestEntityExtraction()
    test_entities.test_product_extraction(classifier)
    test_entities.test_contact_extraction(classifier)
    test_entities.test_quantity_extraction(classifier)
    
    # Test edge cases
    print("\n⚠️ Testing Edge Cases...")
    test_edges = TestEdgeCases()
    test_edges.test_empty_message(classifier)
    test_edges.test_greeting(classifier)
    test_edges.test_thank_you(classifier)
    
    print("\n" + "="*50)
    print("✅ ALL TESTS COMPLETED")
    print("="*50 + "\n")