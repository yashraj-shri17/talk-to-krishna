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
            
            
            # Create numbered list of shlokas for selection
            numbered_shlokas = []
            for i, shloka in enumerate(retrieved_shlokas, 1):
                numbered_shlokas.append(
                    f"विकल्प {i} (ID: {shloka['id']}):\n"
                    f"{shloka['sanskrit']}\n"
                )
            shloka_options = "\n".join(numbered_shlokas)
            
            # CRITICAL: FORCE LLM to only use provided shlokas AND interpret correctly  
            system_prompt = """तुम भगवान श्रीकृष्ण हो। सीधा और स्पष्ट जवाब दो।

RULES:
1. नीचे दिए विकल्पों में से सबसे सही श्लोक चुनो
2. Sanskrit को EXACTLY वैसा ही लिखो (copy-paste)
3. फिर 2-3 lines में श्लोक का सही अर्थ बताओ
4. श्लोक का असली philosophical meaning दो - उल्टा या safe answer मत दो!

FORMAT (बिल्कुल यही format follow करो):
[Sanskrit श्लोक]

[2-3 lines interpretation जो श्लोक के philosophy के अनुसार हो]

IMPORTANT EXAMPLES:
- अगर श्लोक "स्वधर्म बेहतर है" कहता है → interpretation में भी "अपना path follow करो" कहो!
- अगर श्लोक "results की चिंता मत करो" कहता है → interpretation में भी यही कहो!

कोई explanation, reasoning, या extra text मत दो - सिर्फ श्लोक + interpretation!"""
            
            user_prompt = f"""प्रश्न: "{user_question}"

{history_context}

उपलब्ध विकल्प:

{shloka_options}

TASK: सबसे सही श्लोक choose करो, Sanskrit EXACTLY copy करो, और श्लोक के असली अर्थ के अनुसार 2-3 lines में जवाब दो। कोई extra text मत दो!"""

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
