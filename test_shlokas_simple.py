"""
Simple test script to get shlokas for specific questions.
Results are saved to a file for easy viewing.
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

def main():
    """Main test function."""
    # Initialize the API
    print("[LOADING] Initializing Krishna API...")
    api = GitaAPI()
    print("[SUCCESS] API ready!\n")
    
    # Test Questions
    test_questions = [
        "ki mein australia jana chahta hu , but mummy mana kr rhi he toh kya karu mein",
        "मुझे बहुत गुस्सा आता है, मैं कैसे शांत रहूं?",
        "मैं अपने काम में असफल हो गया हूं, अब क्या करूं?",
        "मैं जीवन में बहुत अकेला महसूस करता हूं, मुझे क्या करना चाहिए?"
    ]
    
    # Open output file
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write(" " * 25 + "श्री कृष्ण - श्लोक सुझाव परीक्षण\n")
        f.write("=" * 100 + "\n\n")
        
        for idx, question in enumerate(test_questions, 1):
            print(f"Processing Question {idx}/{len(test_questions)}...")
            
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"प्रश्न {idx}: {question}\n")
            f.write("=" * 100 + "\n\n")
            
            # Get top 5 shlokas
            shlokas = api.search(question, method="hybrid", top_k=5)
            
            if not shlokas:
                f.write("[ERROR] कोई श्लोक नहीं मिला।\n\n")
                continue
            
            f.write(f"[SUCCESS] {len(shlokas)} सर्वश्रेष्ठ श्लोक मिले:\n\n")
            
            for sidx, shloka in enumerate(shlokas, 1):
                f.write(f"{sidx}. गीता {shloka['id']} (अध्याय {shloka['chapter']}, श्लोक {shloka['verse']})\n")
                f.write(f"   संस्कृत: {shloka['sanskrit']}\n")
                f.write(f"   अर्थ: {shloka['meaning']}\n\n")
            
            # Get LLM answer
            f.write("-" * 100 + "\n")
            f.write("श्री कृष्ण का संदेश (LLM Generated Answer):\n")
            f.write("-" * 100 + "\n\n")
            
            result = api.search_with_llm(question)
            if result.get('answer'):
                f.write(result['answer'] + "\n")
            else:
                f.write("[WARNING] LLM उत्तर उपलब्ध नहीं है।\n")
            
            f.write("\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("[SUCCESS] परीक्षण पूर्ण!\n")
        f.write(f"कुल परीक्षित प्रश्न: {len(test_questions)}\n")
        f.write("=" * 100 + "\n")
    
    print("\n[SUCCESS] Results saved to test_results.txt")
    print(f"Total questions tested: {len(test_questions)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
