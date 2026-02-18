"""
Quick test to see which shloka LLM is choosing from the provided list.
"""
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from dotenv import load_dotenv
load_dotenv()

from src.gita_api import GitaAPI

# Initialize API
api = GitaAPI()

# Test question
question = "मैं अपने काम में असफल हो गया हूं, अब क्या करूं?"

# Get shlokas
print("="*80)
print(f"Question: {question}\n")

shlokas = api.search(question, method="hybrid", top_k=5)
print(f"Retrieved {len(shlokas)} shlokas:\n")
for i, s in enumerate(shlokas, 1):
    print(f"{i}. Gita {s['id']}: {s['sanskrit'][:60]}...")

# Get LLM answer
print("\n" + "="*80)
print("LLM Answer:\n")
result = api.search_with_llm(question)
print(result['answer'])
print("="*80)

# Check if LLM used a shloka from the list
retrieved_ids = {s['id'] for s in shlokas}
print(f"\n[DEBUG] Retrieved IDs: {retrieved_ids}")

# Try to find which shloka LLM used
answer = result['answer']
if 'कर्मण्येवाधिकारस्ते' in answer:
    print("[WARNING] LLM used Gita 2.47 (कर्मण्येवाधिकारस्ते)")
    if '2.47' not in retrieved_ids:
        print("[ERROR] Gita 2.47 was NOT in the retrieved list!")
    else:
        print("[SUCCESS] Gita 2.47 was in the retrieved list!")
