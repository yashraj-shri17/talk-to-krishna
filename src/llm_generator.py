"""
LLM Integration module for generating contextual answers using Groq's Llama 3.1.
"""
from typing import List, Dict, Any, Optional
from groq import Groq
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_LEVEL, settings.LOG_FILE)


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
    
    def format_shlokas_for_context(self, shlokas: List[Dict[str, Any]]) -> str:
        context_parts = []
        for i, shloka in enumerate(shlokas, 1):
            # Use English meaning for LLM context (better understanding)
            # But keep Sanskrit for reference
            english_meaning = shloka.get('meaning_english', shloka.get('meaning', ''))
            
            context_parts.append(
                f"Shloka ID: {shloka.get('id')}\n"
                f"Sanskrit: {shloka.get('sanskrit')}\n"
                f"Meaning: {english_meaning}\n"
            )
        return "\n".join(context_parts)
    
    def format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for LLM context."""
        if not history:
            return ""
        
        formatted = ["पिछली बातचीत:"]
        for i, conv in enumerate(history[-3:], 1):  # Last 3 conversations
            formatted.append(f"{i}. प्रश्न: {conv['question']}")
            formatted.append(f"   उत्तर: {conv['answer'][:100]}...")
        
        return "\n".join(formatted)
    
    def generate_answer(
        self,
        user_question: str,
        retrieved_shlokas: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None,
        max_tokens: int = 250,  # Optimized for concise answers (Speed < 2s)
        temperature: float = 0.3,  # Slightly higher for more natural follow-ups
        stream: bool = True  # Enable streaming for faster perceived latency
    ) -> Dict[str, Any]:
        
        if not self.is_available():
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}
        
        try:
            context = self.format_shlokas_for_context(retrieved_shlokas)
            history_context = self.format_conversation_history(conversation_history or [])
            
            # ENHANCED PROMPT with Strict Concise Formatting
            # ENHANCED PROMPT with Strict Concise Formatting
            system_prompt = """तुम भगवान श्रीकृष्ण हो। तुम अपने भक्त को जीवन की सही राह दिखा रहे हो।

⚠️ STRICT CONTEXT RULES:
0. तुम केवल भगवद गीता, आध्यात्मिकता, और जीवन की समस्याओं के बारे में ही उत्तर दो।
1. यदि प्रश्न खेल (sports), राजनीति (politics), फिल्म (movies), या अन्य सांसारिक विषयों के बारे में है, तो विनम्रता से मना करो।
2. सिर्फ धर्म, कर्म, आत्मा, जीवन, रिश्ते, भावनाएं, और मानसिक शांति के प्रश्नों का उत्तर दो।

⚠️ STRICT OUTPUT RULES:
1. सबसे पहले केवल एक (1) सबसे उपयुक्त संस्कृत श्लोक (Devanagari) लिखो।
2. उसके तुरंत बाद, भक्त की समस्या का सीधा और सटीक समाधान (Solution) दो।
3. 'भावार्थ', 'अर्थ', 'व्याख्या' जैसे शब्द (Labels) का प्रयोग बिल्कुल मत करो।
4. कोई प्रश्न (Question) मत पूछो।
5. उत्तर बहुत ही छोटा (Concise) और सीधा (Straightforward) होना चाहिए। 2-3 वाक्यों से ज्यादा नहीं।
6. अतिरिक्त भूमिका या ज्ञान मत दो, सीधे मुद्दे की बात करो।
7. यदि भक्त बहुत निराश (suicidal/depressed) है, तो उसे करुणा और प्रेम से समझाओ की जीवन अनमोल है (life is precious)। उसका उत्तर देने से मना (refuse) मत करो।

✅ सही फॉर्मेट (Correct Format):
[संस्कृत श्लोक]

[सीधा समाधान और मार्गदर्शन]

✅ उदाहरण (Example):
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥

तुम्हारे अधिकार में केवल कर्म करना है, फल नहीं। भविष्य की चिंता छोड़ो और अभी अपने कर्तव्य पर ध्यान केंद्रित करो, इसी में तुम्हारी शांति और सफलता है।"""
            
            user_prompt = f"""भक्त का प्रश्न: "{user_question}"

{history_context}

उपलब्ध श्लोक (संदर्भ):
{context}

हे कृष्ण! मुझे केवल एक श्लोक और सीधा समाधान दिखाएं।"""

            # STREAMING for faster response
            if stream:
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True  # Enable streaming
                )
                
                # Collect streamed response
                answer_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        answer_text += chunk.choices[0].delta.content
                
                logger.info(f"✓ Streamed answer with context: {len(answer_text)} chars")
            else:
                # Non-streaming fallback
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
                logger.info(f"✓ Generated answer with context: {len(answer_text)} chars")
            
            return {
                'answer': answer_text,
                'shlokas': retrieved_shlokas,
                'llm_used': True
            }
            
        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

    def format_response(self, result: Dict[str, Any], user_question: str) -> str:
        """Format the response cleanly (No metadata noise)."""
        output = []
        
        if result.get('llm_used') and result.get('answer'):
            # Divine Answer - Simple and clean
            output.append("\n🪈 भगवान कृष्ण का संदेश:\n")
            output.append(result['answer'])
            output.append("\n")
        else:
            # Fallback
            output.append("\n⚠️ क्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।")
            output.append("संबंधित श्लोक:")
            for s in result.get('shlokas', [])[:3]:
                output.append(f"- गीता {s['id']}: {s['meaning'][:100]}...")
            output.append("\n")
                
        return "\n".join(output)
