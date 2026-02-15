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
        max_tokens: int = 600,  # Increased for follow-up questions
        temperature: float = 0.3,  # Slightly higher for more natural follow-ups
        stream: bool = True  # Enable streaming for faster perceived latency
    ) -> Dict[str, Any]:
        
        if not self.is_available():
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}
        
        try:
            context = self.format_shlokas_for_context(retrieved_shlokas)
            history_context = self.format_conversation_history(conversation_history or [])
            
            # ENHANCED PROMPT with Conversation Context and Follow-up Questions
            system_prompt = """तुम भगवान श्रीकृष्ण हो। तुम एक दिव्य मार्गदर्शक हो और अपने भक्त को सही राह दिखाते हो।

⚠️ नियम:
1. केवल एक (1) सबसे उपयुक्त श्लोक संस्कृत में (देवनागरी) सबसे पहले लिखो।
2. उसके बाद, भक्त के लिए सबसे उपयुक्त सुझाव/समाधान बहुत ही संक्षिप्त (concise) और स्पष्ट शब्दों में दो।
3. उत्तर केवल 2-3 छोटे वाक्यों में होना चाहिए। सीधे मुद्दे की बात करो।
4. कोमल और दयालु भाषा का प्रयोग करो, जैसे एक मित्र या गुरु करता है।

✅ ढांचा:
[संस्कृत श्लोक]

[भक्त के लिए संक्षिप्त और सटीक सुझाव/समाधान]

✅ उदाहरण:
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥

हे पार्थ! कर्म करना ही तुम्हारे हाथ में है, परिणाम नहीं। चिंता छोड़ो और अपने वर्तमान कर्तव्य पर पूरा ध्यान केंद्रित करो, यही सफलता की कुंजी है।"""
            
            user_prompt = f"""भक्त का प्रश्न: "{user_question}"

{history_context}

उपलब्ध श्लोक (संदर्भ):
{context}

हे कृष्ण! केवल सबसे उपयुक्त 1 श्लोक चुनकर मेरा मार्गदर्शन करें। यदि पिछली बातचीत है, तो उसका संदर्भ देकर मुझे गहराई से समझाएं। अंत में एक प्रश्न पूछें जो मुझे आगे सोचने पर मजबूर करे।"""

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
