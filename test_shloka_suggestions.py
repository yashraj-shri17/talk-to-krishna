"""
Test script to demonstrate shloka suggestions for various questions.
This script runs test questions and shows the top 4-5 shlokas suggested by the model.
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gita_api import GitaAPI
from src.logger import setup_logger

logger = setup_logger(__name__, "INFO", "test_shlokas.log")

def print_separator():
    """Print a visual separator."""
    print("\n" + "="*100 + "\n")

def print_shloka(shloka, index):
    """Print a single shloka in a formatted way."""
    print(f"\n{index}. गीता {shloka['id']} (Chapter {shloka['chapter']}, Verse {shloka['verse']})")
    print(f"   संस्कृत: {shloka['sanskrit']}")
    print(f"   अर्थ: {shloka['meaning'][:200]}...")
    if len(shloka['meaning']) > 200:
        print(f"        ...{shloka['meaning'][200:400]}...")
    print()

def test_question(api, question, question_number):
    """Test a single question and display the top 5 shlokas."""
    print_separator()
    print(f"प्रश्न {question_number}: {question}")
    print_separator()
    
    # Get top 5 shlokas (without LLM answer for now, just retrieval)
    try:
        shlokas = api.search(question, method="hybrid", top_k=5)
        
        if not shlokas:
            print("[ERROR] कोई श्लोक नहीं मिला।\n")
            return
        
        print(f"[SUCCESS] {len(shlokas)} सर्वश्रेष्ठ श्लोक मिले:\n")
        
        for idx, shloka in enumerate(shlokas, 1):
            print_shloka(shloka, idx)
        
        # Also get the LLM-generated answer
        print("\n" + "-"*100)
        print("श्री कृष्ण का संदेश (LLM Generated Answer):")
        print("-"*100 + "\n")
        
        result = api.search_with_llm(question)
        if result.get('answer'):
            print(result['answer'])
        else:
            print("[WARNING] LLM उत्तर उपलब्ध नहीं है।")
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        print(f"[ERROR] त्रुटि: {e}\n")

def main():
    """Main test function."""
    print("\n" + "="*100)
    print(" "*25 + "श्री कृष्ण - श्लोक सुझाव परीक्षण")
    print("="*100 + "\n")
    
    # Initialize the API
    print("[LOADING] Krishna API को लोड कर रहे हैं...\n")
    api = GitaAPI()
    print("[SUCCESS] API तैयार है!\n")
    
    # Test Questions
    test_questions = [
        "ki mein australia jana chahta hu , but mummy mana kr rhi he toh kya karu mein",
        "मुझे बहुत गुस्सा आता है, मैं कैसे शांत रहूं?",
        "मैं अपने काम में असफल हो गया हूं, अब क्या करूं?",
        "मैं जीवन में बहुत अकेला महसूस करता हूं, मुझे क्या करना चाहिए?"
    ]
    
    # Test each question
    for idx, question in enumerate(test_questions, 1):
        test_question(api, question, idx)
    
    # Final summary
    print_separator()
    print("[SUCCESS] परीक्षण पूर्ण!")
    print(f"कुल परीक्षित प्रश्न: {len(test_questions)}")
    print_separator()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] परीक्षण रद्द किया गया।")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[FATAL ERROR] गंभीर त्रुटि: {e}")
        sys.exit(1)
