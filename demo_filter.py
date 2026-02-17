"""
Simple demo to show context filtering in action.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gita_api import GitaAPI

def demo_filtering():
    """Demo the context relevance filter."""
    
    print("Initializing Krishna API...")
    api = GitaAPI()
    api._load_resources()
    print("✅ API Ready!\n")
    
    # Test out-of-context questions
    out_of_context_queries = [
        "India vs Pakistan match update?",
        "Who is Donald Trump?",
        "Best pizza recipe",
    ]
    
    # Test valid questions
    valid_queries = [
        "How to control anger?",
        "What is the meaning of life?",
    ]
    
    print("="*80)
    print("TESTING OUT-OF-CONTEXT QUESTIONS (Should be REJECTED)")
    print("="*80)
    
    for query in out_of_context_queries:
        print(f"\n📝 Query: {query}")
        result = api.search_with_llm(query)
        is_rejected = result.get('rejected', False)
        
        if is_rejected:
            print("✅ Status: REJECTED (as expected)")
            print(f"Response:\n{result['answer']}\n")
        else:
            print("❌ Status: NOT REJECTED (unexpected!)")
            print(f"Answer: {result.get('answer', '')[:100]}...")
    
    print("\n" + "="*80)
    print("TESTING VALID QUESTIONS (Should be ACCEPTED)")
    print("="*80)
    
    for query in valid_queries:
        print(f"\n📝 Query: {query}")
        result = api.search_with_llm(query)
        is_rejected = result.get('rejected', False)
        
        if not is_rejected:
            print("✅ Status: ACCEPTED (as expected)")
            print(f"Answer preview: {result.get('answer', '')[:150]}...")
        else:
            print("❌ Status: REJECTED (unexpected!)")
            print(f"Rejection: {result['answer'][:100]}...")

if __name__ == "__main__":
    demo_filtering()
