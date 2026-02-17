"""
Test script to verify context relevance filtering.
Tests that the model correctly rejects out-of-context questions.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gita_api import GitaAPI

def test_relevance_filter():
    """Test the relevance filtering with various queries."""
    
    print("Initializing Krishna API...")
    api = GitaAPI()
    api._load_resources()
    print("✅ API Ready!\n")
    
    # Test cases: (query, should_be_accepted)
    test_cases = [
        # Should be REJECTED (out of context)
        ("India vs Pakistan match update?", False),
        ("Who is Donald Trump?", False),
        ("What is the capital of France?", False),
        ("Best pizza recipe", False),
        ("iPhone 15 price in India", False),
        ("Who won the world cup 2023?", False),
        ("Tell me a movie recommendation", False),
        
        # Should be ACCEPTED (Krishna/Gita related or life guidance)
        ("How to control anger?", True),
        ("What is the meaning of life?", True),
        ("I am feeling depressed, what should I do?", True),
        ("What does Bhagavad Gita say about karma?", True),
        ("How to find peace in life?", True),
        ("I failed in my exam, please help", True),
        ("जीवन का उद्देश्य क्या है?", True),
        ("Hi Krishna", True),  # Greeting
    ]
    
    print("="*80)
    print("TESTING CONTEXT RELEVANCE FILTER")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for query, should_accept in test_cases:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"Expected: {'✅ ACCEPT' if should_accept else '❌ REJECT'}")
        
        result = api.search_with_llm(query)
        is_rejected = result.get('rejected', False)
        is_greeting = "राधे राधे" in result.get('answer', '')
        
        # Determine actual result
        actual_accept = not is_rejected
        
        # Check if result matches expectation
        if actual_accept == should_accept or (is_greeting and should_accept):
            print(f"Result: ✅ PASS")
            passed += 1
            if is_rejected:
                print(f"Rejection message: {result['answer'][:100]}...")
        else:
            print(f"Result: ❌ FAIL")
            print(f"Got rejected={is_rejected}, expected acceptance={should_accept}")
            if result.get('answer'):
                print(f"Answer preview: {result['answer'][:150]}...")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Context filtering is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Review the implementation.")

if __name__ == "__main__":
    test_relevance_filter()
