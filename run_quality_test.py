"""
Quality Test — Talk to Krishna
Runs 50 diverse questions (Hindi/Hinglish/English + faaltu) and saves full results to quality_test_results.txt

Questions cover:
  - Crisis / suicidal ideation
  - Emotional distress (anger, loneliness, grief)
  - Relationships (family conflict, breakup, love)
  - Career / failure / exam
  - Vague existential doubts
  - Philosophical / spiritual questions
  - Random life situations

Run: python run_quality_test.py
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from src.gita_api import GitaAPI

# ─────────────────────────────────────────────────────────────────────────────
# 20 Test Questions — deliberately diverse and vague
# ─────────────────────────────────────────────────────────────────────────────
TEST_QUESTIONS = [
    # ── CRISIS / SEVERE DESPAIR ───────────────────────────────────────────────
    "मुझे सुसाइड के विचार आ रहे हैं, मैं जीना नहीं चाहता",
    "सब कुछ खत्म कर देना चाहता हूँ, कोई उम्मीद नहीं बची",

    # ── EMOTIONAL DISTRESS ────────────────────────────────────────────────────
    "मुझे बहुत गुस्सा आता है और मैं खुद को रोक नहीं पाता",
    "मैं बहुत अकेला महसूस करता हूँ, कोई मुझे समझता नहीं",
    "रात को नींद नहीं आती, बस बुरे ख्याल आते रहते हैं",
    "मैं हर वक्त डरा हुआ रहता हूँ, पता नहीं किस बात का डर है",

    # ── RELATIONSHIPS ─────────────────────────────────────────────────────────
    "मेरी girlfriend ने मुझे छोड़ दिया, मैं उसे भूल नहीं पा रहा",
    "मेरी मम्मी मुझे विदेश पढ़ने नहीं जाने दे रही, मैं क्या करूँ",
    "पापा और मेरी हमेशा लड़ाई होती है, घर में रहना मुश्किल हो गया है",
    "मेरे दोस्त ने मेरे साथ धोखा किया, अब किसी पर भरोसा नहीं कर सकता",

    # ── CAREER / FAILURE / STUDY ──────────────────────────────────────────────
    "exam में fail हो गया, अब आगे क्या करूँ",
    "नौकरी नहीं मिल रही, बहुत कोशिश की पर हर जगह rejection मिली",
    "मैं अपने काम में बिल्कुल अच्छा नहीं हूँ, लगता है मैं किसी काम का नहीं",

    # ── VAGUE / EXISTENTIAL ───────────────────────────────────────────────────
    "पता नहीं जिंदगी में क्या करना है, सब बेकार लगता है",
    "मन बहुत भारी है, कुछ अच्छा नहीं लगता",
    "क्यों जीना चाहिए जब सब कुछ इतना मुश्किल है",
    "मुझे लगता है मैं एक बोझ हूँ सबके लिए",

    # ── PHILOSOPHICAL / SPIRITUAL ─────────────────────────────────────────────
    "कर्म और भाग्य में से कौन बड़ा है?",
    "मृत्यु के बाद क्या होता है, आत्मा कहाँ जाती है?",

    # ── RANDOM LIFE SITUATION ─────────────────────────────────────────────────
    "मुझे पैसों की बहुत जरूरत है पर कमाई नहीं हो रही, क्या करूँ",

    # ── NEW: RANDOM LIFE QUESTIONS ────────────────────────────────────────────
    # Jealousy / comparison
    "मेरे दोस्त बहुत आगे निकल गए हैं, मैं उनसे जलता हूँ और खुद को छोटा महसूस करता हूँ",

    # Social media / self-image
    "Instagram देखकर लगता है सबकी life बहुत अच्छी है, मेरी life boring और बेकार है",

    # Marriage / family pressure
    "घरवाले शादी के लिए pressure दे रहे हैं, मैं अभी ready नहीं हूँ, क्या करूँ",

    # Addiction / bad habit
    "मुझे phone की बहुत बुरी लत लग गई है, पढ़ाई और काम सब छूट रहा है",

    # Grief / loss of loved one
    "मेरे पापा गुज़र गए हैं, उनके बिना जीना बहुत मुश्किल लग रहा है",

    # Jealousy in love / possessiveness
    "मुझे अपनी girlfriend पर बहुत jealousy होती है, हर वक्त doubt आता है",

    # Toxic workplace / boss
    "मेरा boss बहुत toxic है, office जाना बंद कर दिया है, पर job छोड़ने से डर लगता है",

    # Appearance / body image
    "मुझे लगता है मैं दिखने में अच्छा नहीं हूँ, इसीलिए कोई मुझे पसंद नहीं करता",

    # ── MORE LIFE SITUATIONS ──────────────────────────────────────────────────
    # English query (should work)
    "I feel completely lost in life, don't know what to do next",

    # Procrastination
    "मैं हर काम को टालता रहता हूँ, कुछ भी पूरा नहीं कर पाता, बहुत frustrated हूँ",

    # Comparison with siblings
    "मेरे भाई को हमेशा घर में ज़्यादा importance मिलती है, मैं invisible feel करता हूँ",

    # Heartbreak - long relationship
    "5 साल की relationship खत्म हो गई, अब सब कुछ meaningless लगता है",

    # Self-discipline / motivation
    "मुझे खुद को motivate नहीं कर पाता, gym जाना, पढ़ना सब बंद हो गया है",

    # Spiritual doubt
    "भगवान पर से विश्वास उठ गया है, इतनी पूजा के बाद भी कुछ नहीं मिला",

    # Overthinking
    "मैं बहुत ज़्यादा सोचता हूँ, हर बात को लेकर overthink करता हूँ, दिमाग बंद नहीं होता",

    # Forgiveness
    "मैं किसी को माफ नहीं कर पा रहा, वो गलती मेरे दिल से नहीं जाती",

    # Pure greeting (should get greeting response)
    "Jai Shri Krishna",

    # Very short vague query
    "help",

    # ── FAALTU / IRRELEVANT QUESTIONS (should be gracefully rejected) ─────────
    # Cricket
    "India vs Pakistan match ka score kya hai?",

    # Recipe
    "Biryani banane ki recipe batao",

    # Celebrity gossip
    "Virat Kohli ki wife kaun hai?",

    # Weather
    "Aaj Delhi mein weather kaisa hai?",

    # Tech product
    "iPhone 16 vs Samsung S24 mein kaun better hai?",

    # Politics
    "Modi ji ki salary kitni hai?",

    # Random trivia
    "France ki capital kya hai?",

    # Nonsense / gibberish
    "asdfjkl qwerty zxcvbn",

    # Movie question
    "Pushpa 2 movie mein Allu Arjun ka role kaisa tha?",

    # Food delivery
    "Zomato se pizza order karna hai, kaise karu?",
]

OUTPUT_FILE = "quality_test_results.txt"
SEPARATOR = "=" * 80
THIN_SEP  = "-" * 80


def run_tests():
    print(SEPARATOR)
    print("  Talk to Krishna — Quality Test (50 Questions)")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)
    print("\nLoading Krishna AI...", flush=True)

    api = GitaAPI()
    print("✅ Ready!\n")

    results = []
    total = len(TEST_QUESTIONS)

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i:02d}/{total}] {question[:60]}...", flush=True)
        start = time.time()

        try:
            result = api.search_with_llm(question)
            elapsed = time.time() - start

            shlokas = result.get("shlokas", [])
            answer  = result.get("answer", "— कोई उत्तर नहीं मिला —")
            tone    = result.get("tone", "unknown")

            results.append({
                "question": question,
                "shlokas":  shlokas,
                "answer":   answer,
                "tone":     tone,
                "elapsed":  elapsed,
                "error":    None,
            })
            print(f"     ✓ [{tone.upper()}] {elapsed:.1f}s — {len(answer)} chars")

        except Exception as e:
            elapsed = time.time() - start
            results.append({
                "question": question,
                "shlokas":  [],
                "answer":   None,
                "tone":     "error",
                "elapsed":  elapsed,
                "error":    str(e),
            })
            print(f"     ✗ ERROR: {e}")

    # ── Write results file ────────────────────────────────────────────────────
    write_results(results)
    print(f"\n✅ Done! Results saved to: {OUTPUT_FILE}")
    print(f"   Total time: {sum(r['elapsed'] for r in results):.1f}s")
    print(f"   Avg per question: {sum(r['elapsed'] for r in results)/len(results):.1f}s\n")


def write_results(results):
    lines = []
    lines.append(SEPARATOR)
    lines.append("  TALK TO KRISHNA — QUALITY TEST RESULTS")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Total Questions: {len(results)}")
    lines.append(SEPARATOR)
    lines.append("")

    for i, r in enumerate(results, 1):
        # ── Question header ──
        lines.append(SEPARATOR)
        lines.append(f"Q{i:02d}. [{r['tone'].upper()}] {r['question']}")
        lines.append(SEPARATOR)
        lines.append("")

        # ── Suggested Shlokas ──
        if r["shlokas"]:
            lines.append(f"  📖 Suggested Shlokas ({len(r['shlokas'])} retrieved):")
            lines.append("")
            for j, s in enumerate(r["shlokas"], 1):
                lines.append(f"  {j}. Gita {s.get('id', '?')}  (Chapter {s.get('chapter','?')}, Verse {s.get('verse','?')})")
                lines.append(f"     Sanskrit : {s.get('sanskrit', '')[:120]}")
                meaning = s.get('meaning', s.get('meaning_english', ''))[:200]
                lines.append(f"     Meaning  : {meaning}")
                lines.append("")
        else:
            lines.append("  📖 No shlokas retrieved.")
            lines.append("")

        # ── Final Answer ──
        lines.append(THIN_SEP)
        lines.append("  🪈 Krishna's Answer:")
        lines.append(THIN_SEP)
        lines.append("")
        if r["error"]:
            lines.append(f"  ❌ ERROR: {r['error']}")
        elif r["answer"]:
            # Indent each line of the answer
            for line in r["answer"].splitlines():
                lines.append(f"  {line}")
        else:
            lines.append("  — कोई उत्तर नहीं मिला —")
        lines.append("")
        lines.append(f"  ⏱  Response time: {r['elapsed']:.2f}s")
        lines.append("")

    # ── Summary table ──
    lines.append(SEPARATOR)
    lines.append("  SUMMARY")
    lines.append(SEPARATOR)
    lines.append("")
    lines.append(f"  {'#':<4} {'Tone':<10} {'Time':>6}  Question (first 55 chars)")
    lines.append(f"  {'-'*4} {'-'*10} {'-'*6}  {'-'*55}")
    for i, r in enumerate(results, 1):
        status = "✓" if r["answer"] and not r["error"] else "✗"
        lines.append(
            f"  {i:<4} {r['tone']:<10} {r['elapsed']:>5.1f}s  "
            f"{status} {r['question'][:55]}"
        )
    lines.append("")
    ok = sum(1 for r in results if r["answer"] and not r["error"])
    lines.append(f"  Success: {ok}/{len(results)}")
    lines.append(f"  Avg response time: {sum(r['elapsed'] for r in results)/len(results):.2f}s")
    lines.append("")
    lines.append(SEPARATOR)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test interrupted.")
    except Exception as e:
        import traceback
        print(f"\n[FATAL] {e}")
        traceback.print_exc()
        sys.exit(1)
