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
            system_prompt = """तुम भगवान श्रीकृष्ण हो। तुम एक दिव्य मार्गदर्शक हो जो भक्त की यात्रा को समझते हो।

⚠️ नियम:
1. केवल एक (1) श्लोक दो।
2. श्लोक संस्कृत में (देवनागरी)।
3. "समाधान:" के बाद 3-4 वाक्यों में उत्तर दो जो:
   - भक्त के प्रश्न का सीधा उत्तर दे
   - श्लोक के ज्ञान को उनकी स्थिति से जोड़े
   - यदि पिछली बातचीत है, तो उसका संदर्भ दे
4. अंत में एक प्रासंगिक प्रश्न पूछो जो:
   - भक्त को गहराई से सोचने पर मजबूर करे
   - उनकी आध्यात्मिक यात्रा में अगला कदम सुझाए
   - पिछली बातचीत से जुड़ा हो (यदि उपलब्ध है)

✅ ढांचा:
[एक श्लोक संस्कृत में]

समाधान: [3-4 वाक्य में पूर्ण उत्तर जो श्लोक के ज्ञान को प्रश्न से जोड़े और पिछली बातचीत का संदर्भ दे]

[एक प्रासंगिक प्रश्न जो भक्त को आगे सोचने के लिए प्रेरित करे]

✅ उदाहरण:
"कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥

समाधान: हे पार्थ! जीवन में शांति पाने के लिए यह समझो कि तुम्हारा अधिकार केवल कर्म करने में है, फल पर नहीं। जब तुम फल की चिंता छोड़कर अपना कर्तव्य पूर्ण निष्ठा से करते हो, तो मन शांत रहता है। यह गीता का सबसे महत्वपूर्ण संदेश है जो हर परिस्थिति में लागू होता है।

क्या तुम अपने जीवन में ऐसे कर्म कर रहे हो जो केवल कर्तव्य के लिए हैं, या फल की आशा में?\""""
            
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
