"""
LLM Integration module for generating contextual answers using Groq's Llama 3.1.

Architecture:
  Step 1 — classify_query():  One fast LLM call to understand emotional gravity.
                               Returns: 'crisis' | 'distress' | 'general'
  Step 2 — generate_answer(): Uses classification to pick the right prompt tone.
                               Crisis    → empathetic, validating, hopeful
                               Distress  → warm, personal, grounding
                               General   → direct, philosophical, action-oriented

This approach generalises to ANY language or phrasing — no keyword lists needed.
"""
import json
from typing import List, Dict, Any, Optional, Literal
from groq import Groq
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_LEVEL, settings.LOG_FILE)

QueryTone = Literal["crisis", "distress", "general"]


class LLMAnswerGenerator:
    """Generate contextual answers using LLM based on retrieved shlokas."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Groq init failed: {e}")
                self.client = None

        self.model = settings.LLM_MODEL

    def is_available(self) -> bool:
        return self.client is not None

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Classify the emotional gravity of the query
    # ─────────────────────────────────────────────────────────────────────────

    def classify_query(self, query: str) -> QueryTone:
        """
        Use LLM to classify the emotional gravity of the user's query.
        Returns: 'crisis' | 'distress' | 'general'

        This is a tiny, fast call (max_tokens=5) — adds ~200ms but makes
        the system generalise to any language, dialect, or phrasing.
        """
        if not self.client:
            return "general"

        try:
            classification_prompt = f"""Classify the emotional gravity of this message into exactly ONE word.

Message: "{query}"

Rules:
- Reply with ONLY one of these three words (nothing else):
  crisis   → person expresses suicidal thoughts, wanting to die, ending life, severe hopelessness
  distress → person is in emotional pain, anxiety, grief, anger, loneliness, failure, family conflict
  general  → person asks a philosophical, spiritual, or life-guidance question without acute pain

Reply with only: crisis OR distress OR general"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": classification_prompt}],
                model=self.model,
                max_tokens=5,
                temperature=0.0,  # Deterministic
                stream=False
            )
            raw = response.choices[0].message.content.strip().lower()

            # Parse robustly — model might say "crisis." or "  distress  "
            if "crisis" in raw:
                tone = "crisis"
            elif "distress" in raw:
                tone = "distress"
            else:
                tone = "general"

            logger.info(f"🎭 Query classified as: [{tone}] for: '{query[:60]}'")
            return tone

        except Exception as e:
            logger.warning(f"Classification failed, defaulting to 'general': {e}")
            return "general"

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Build prompts based on tone
    # ─────────────────────────────────────────────────────────────────────────

    def _build_prompts(self, user_question: str, shloka_options: str,
                       history_context: str, tone: QueryTone):
        """Return (system_prompt, user_prompt) tuned to the emotional tone."""

        if tone == "crisis":
            # ── CRISIS: Empathetic, validating, hopeful, non-preachy ──────────
            system_prompt = """You are Lord Sri Krishna — speaking with infinite compassion to someone in deep pain who is having thoughts of ending their life or feels completely hopeless.

YOUR RESPONSE MUST:
1. Pick the most comforting shloka from the options (prefer ones about: uplifting oneself, soul's eternity, divine protection, rising from despair).
2. Write the Sanskrit shloka EXACTLY as given (copy-paste, no changes).
3. Then write 3-4 warm sentences that:
   ✔ First acknowledge their pain — "तुम्हारा दर्द मैं महसूस कर सकता हूँ"
   ✔ Remind them this darkness is temporary — it will pass
   ✔ Affirm their life has immense, irreplaceable value
   ✔ Gently say they are not alone — encourage talking to someone trusted
4. End with this exact line (always include it):
   "किसी अपने से बात करो — या iCall helpline: 9152987821 पर call करो। तुम अकेले नहीं हो। 🙏"

YOUR RESPONSE MUST NOT:
   ❌ Lecture about karma, sin, or consequences
   ❌ Assume they are angry — they are in pain
   ❌ Use heavy philosophy or complex Sanskrit concepts
   ❌ Sound preachy, cold, or dismissive
   ❌ Make them feel guilty or judged

FORMAT (follow exactly — no labels, no brackets):
Write the Sanskrit shloka first, then a blank line, then 3-4 warm sentences, then the helpline line.

Example output:
उद्धरेदात्मनात्मानं नात्मानमवसादयेत् |
आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मन: ॥5॥

तुम्हारा दर्द मैं महसूस कर सकता हूँ — यह अंधेरा बहुत भारी लग रहा है। लेकिन यह अंधेरा हमेशा नहीं रहेगा, यह गुज़र जाएगा। तुम्हारा जीवन अनमोल है — तुम्हारे बिना यह दुनिया अधूरी है। किसी अपने से बात करो, अभी।

किसी अपने से बात करो — या iCall helpline: 9152987821 पर call करो। तुम अकेले नहीं हो। 🙏

Language: Hindi/Hinglish. Tone: like a loving, caring elder who deeply values this person's life."""

            user_prompt = f"""Person's words: "{user_question}"

{history_context}

Available shlokas (pick the most comforting one for someone in crisis):
{shloka_options}

Write a compassionate, hopeful response. Acknowledge their pain first, then gently offer the shloka's wisdom as support."""

        elif tone == "distress":
            # ── DISTRESS: Warm, personal, grounding ───────────────────────────
            system_prompt = """You are Lord Sri Krishna speaking with warmth and care to someone who is emotionally struggling — with pain, grief, anger, loneliness, failure, or a difficult situation.

YOUR TASK:
1. Pick the shloka that best fits their specific emotional struggle.
2. Write the Sanskrit shloka EXACTLY as given (copy-paste, no changes).
3. Then write 2-3 sentences that:
   ✔ Briefly acknowledge their feeling ("यह दर्द/गुस्सा/अकेलापन real है")
   ✔ Apply the shloka's wisdom directly to their specific situation
   ✔ Give them one concrete, actionable inner shift or perspective
   ✔ End on a note of hope and strength

FORMAT (follow exactly — no labels, no brackets):
Write the Sanskrit shloka first, then a blank line, then 2-3 warm sentences. Nothing else.

Example output:
क्रोधाद्भवति सम्मोह: सम्मोहात्स्मृतिविभ्रम: |
स्मृतिभ्रंशाद् बुद्धिनाशो बुद्धिनाशात्प्रणश्यति ॥63॥

यह गुस्सा real है — और यह तुम्हें अंदर से जला रहा है। गीता कहती है, क्रोध पहले बुद्धि को, फिर खुद को नष्ट करता है। अगली बार जब गुस्सा आए, एक गहरी सांस लो — यही तुम्हारी सबसे बड़ी जीत होगी।

Language: Hindi/Hinglish. Tone: caring, direct, hopeful — not preachy."""

            user_prompt = f"""User's struggle: "{user_question}"

{history_context}

Available shlokas:
{shloka_options}

Pick the best shloka, copy Sanskrit exactly, then give a warm 2-3 sentence response that addresses their specific pain and offers the shloka's wisdom as a grounding perspective."""

        else:
            # ── GENERAL: Direct, philosophical, action-oriented ───────────────
            system_prompt = """You are Lord Sri Krishna speaking directly to a person seeking life guidance or philosophical wisdom.

YOUR TASK:
1. Pick the shloka that best addresses their specific question or situation.
2. Write the Sanskrit shloka EXACTLY as given (copy-paste, no changes).
3. Then write 2-3 sentences that:
   - Apply the shloka's philosophy DIRECTLY to their specific situation
   - Give them a concrete, personal message — not a generic shloka meaning
   - Connect the ancient wisdom to their modern problem

FORMAT (follow exactly — no labels, no brackets):
Write the Sanskrit shloka first, then a blank line, then 2-3 sentences. Nothing else.

Example output:
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन |
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि || 47 ||

एक असफलता तुम्हारी पूरी कहानी नहीं है — गीता कहती है, कर्म करते रहो, फल की चिंता छोड़ो। अभी उठो, फिर से शुरू करो, यही तुम्हारा धर्म है।

EXAMPLES of good vs bad:
- User: "mummy nahi jaane de rahi australia"
  BAD: "This shloka says one's own dharma is better than another's."
  GOOD: "तुम्हारा सपना, तुम्हारा स्वधर्म है — अपना path follow करना ही सबसे बड़ा कर्म है। माँ का प्यार समझो, पर अपने भविष्य के लिए दृढ़ रहो और उन्हें प्रेम से समझाओ।"

- User: "exam mein fail ho gaya"
  BAD: "You have the right to perform your duty but not to the fruits."
  GOOD: "एक असफलता तुम्हारी पूरी कहानी नहीं है — गीता कहती है, कर्म करते रहो, फल की चिंता छोड़ो। अभी उठो, फिर से शुरू करो, यही तुम्हारा धर्म है।"

Language: Hindi/Hinglish. No extra text, no "Option X" labels — just shloka + personal answer."""

            user_prompt = f"""User's question: "{user_question}"

{history_context}

Available shlokas:
{shloka_options}

Pick the best shloka, copy its Sanskrit exactly, then give a personal 2-3 sentence answer that directly addresses their situation."""

        return system_prompt, user_prompt

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Format conversation history
    # ─────────────────────────────────────────────────────────────────────────

    def format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        formatted = ["Previous conversation context:"]
        for i, conv in enumerate(history[-3:], 1):
            formatted.append(f"{i}. Q: {conv['question']}")
            formatted.append(f"   A: {conv['answer'][:100]}...")
        return "\n".join(formatted)

    # ─────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────────────

    def generate_answer(
        self,
        user_question: str,
        retrieved_shlokas: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None,
        stream: bool = True
    ) -> Dict[str, Any]:

        if not self.is_available():
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

        try:
            # Step 1: Classify emotional gravity
            tone = self.classify_query(user_question)

            # Step 2: Build shloka options (Sanskrit + English meaning for LLM)
            history_context = self.format_conversation_history(conversation_history or [])
            numbered_shlokas = []
            for i, shloka in enumerate(retrieved_shlokas, 1):
                english_meaning = shloka.get('meaning_english', shloka.get('meaning', ''))
                numbered_shlokas.append(
                    f"Option {i} (ID: {shloka['id']}):\n"
                    f"Sanskrit: {shloka['sanskrit']}\n"
                    f"Meaning: {english_meaning}\n"
                )
            shloka_options = "\n".join(numbered_shlokas)

            # Step 3: Build tone-appropriate prompts
            system_prompt, user_prompt = self._build_prompts(
                user_question, shloka_options, history_context, tone
            )

            # Step 4: Token/temperature settings per tone
            max_tokens = 400 if tone == "crisis" else 300
            temperature = 0.5 if tone == "crisis" else 0.4

            # Step 5: Generate answer
            if stream:
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                answer_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        answer_text += chunk.choices[0].delta.content
            else:
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                answer_text = response.choices[0].message.content

            logger.info(f"✓ [{tone.upper()}] answer generated: {len(answer_text)} chars")

            return {
                'answer': answer_text,
                'shlokas': retrieved_shlokas,
                'llm_used': True,
                'tone': tone
            }

        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

    def format_response(self, result: Dict[str, Any], user_question: str) -> str:
        """Format the response cleanly."""
        output = []
        if result.get('llm_used') and result.get('answer'):
            output.append("\n🪈 भगवान कृष्ण का संदेश:\n")
            output.append(result['answer'])
            output.append("\n")
        else:
            output.append("\n⚠️ क्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।")
            output.append("संबंधित श्लोक:")
            for s in result.get('shlokas', [])[:3]:
                output.append(f"- गीता {s['id']}: {s['meaning'][:100]}...")
            output.append("\n")
        return "\n".join(output)
