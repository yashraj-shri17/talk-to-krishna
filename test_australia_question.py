"""
Quick test for the Australia question to see if keyword mappings work
"""
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from src.gita_api import GitaAPI

api = GitaAPI()

question = "ki mein australia jana chahta hu , but mummy mana kr rhi he toh kya karu mein"

print("="*80)
print(f"Question: {question}\n")

# Get retrieved shlokas
result = api.search(question, method='hybrid', top_k=5)

print(f"Top 5 Retrieved Shlokas:\n")
for i, s in enumerate(result, 1):
    print(f"{i}. Gita {s['id']}: {s.get('meaning', s.get('meaning_hindi', ''))[:100]}...")

# Get LLM answer
print("\n" + "="*80)
print("LLM Answer:\n")
llm_result = api.search_with_llm(question)
print(llm_result['answer'])
print("="*80)
