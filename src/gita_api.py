"""
Unified Production-Grade API for Talk to Krishna.
Implements multi-stage retrieval RAG system.
"""
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Literal
from fastembed import TextEmbedding
# from sentence_transformers import SentenceTransformer, CrossEncoder # REMOVED for memory efficiency
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

from src.config import settings
from src.logger import setup_logger
from src.llm_generator import LLMAnswerGenerator
from src.exceptions import InvalidInputError

logger = setup_logger(__name__, settings.LOG_LEVEL, settings.LOG_FILE)

SearchMethod = Literal["hybrid"]  # Only best method remains

class GitaAPI:
    """
    Production-grade RAG system for Bhagavad Gita.
    
    Pipeline:
    1. LLM Query Understanding (extracts topic/concepts)
    2. Hybrid Search (Multilingual Semantic + Keyword)
    3. Cross-Encoder Re-ranking
    4. LLM Answer Generation
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize system."""
        self.groq_api_key = groq_api_key or settings.GROQ_API_KEY
        
        # Models (Lazy loaded)
        self.semantic_model = None
        self.cross_encoder = None
        self.groq_client = None
        
        # Data
        self.embeddings = None
        self.shlokas = []
        
        # LLM
        self.llm_generator = None
        
        logger.info("GitaAPI initialized (Production Mode)")
    
    def _load_resources(self):
        """Load all data and models if not loaded."""
        if self.shlokas and self.semantic_model:
            return

        logger.info("Loading high-performance models & data...")
        
        # 1. Load Data
        print("Loading Bhagavad Gita verses...")
        
        # Try to load English version first (better for search)
        english_file = Path(settings.gita_emotions_path.parent / "gita_english.json")
        
        if english_file.exists():
            print("   Using English translations for better semantic search")
            with open(english_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chapters = data.get('chapters', {})
                self.shlokas = []
                for c_num, c_data in chapters.items():
                    for v_num, v_data in c_data.items():
                        # Use English for search, Hindi for display
                        english_meaning = v_data.get('meaning_english', '')
                        hindi_meaning = v_data.get('meaning_hindi', v_data.get('meaning', ''))
                        text = v_data.get('text', '')
                        
                        self.shlokas.append({
                            'id': f"{c_num}.{v_num}",
                            'chapter': int(c_num),
                            'verse': int(v_num),
                            'sanskrit': text,
                            'meaning': hindi_meaning,  # Hindi for display to user
                            'meaning_english': english_meaning,  # English for search
                            # Create rich searchable text with English + Sanskrit
                            'searchable_text': f"{english_meaning} {text}".lower()
                        })
        else:
            # Fallback to Hindi-only version
            print("   English translations not found, using Hindi")
            print("   Run 'python translate_to_english.py' for better search quality")
            
            if not settings.gita_emotions_path.exists():
                raise FileNotFoundError(f"Data missing: {settings.gita_emotions_path}")
                
            with open(settings.gita_emotions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chapters = data.get('chapters', {})
                self.shlokas = []
                for c_num, c_data in chapters.items():
                    for v_num, v_data in c_data.items():
                        meaning = v_data.get('meaning', '')
                        text = v_data.get('text', '')
                        self.shlokas.append({
                            'id': f"{c_num}.{v_num}",
                            'chapter': int(c_num),
                            'verse': int(v_num),
                            'sanskrit': text,
                            'meaning': meaning,
                            'meaning_english': meaning,  # Same as Hindi if no English
                            # Create rich searchable text
                            'searchable_text': f"{meaning} {text}".lower()
                        })
        
        print(f"   {len(self.shlokas)} shlokas loaded")
        logger.info(f"Loaded {len(self.shlokas)} shlokas")

        # 2. Load Embeddings
        print("Loading semantic understanding...")
        if not settings.embeddings_path.exists():
             raise FileNotFoundError(f"Embeddings missing. Run rebuild_embeddings.py first!")
             
        with open(settings.embeddings_path, 'rb') as f:
            data = pickle.load(f)
            self.embeddings = data['embeddings']
            # Safety check: Ensure model matches
            saved_model_name = data.get('model_name', '')
            configured_model = settings.SENTENCE_TRANSFORMER_MODEL
            if saved_model_name and saved_model_name != configured_model:
                logger.warning(f"Model mismatch! Saved: {saved_model_name}, Config: {configured_model}")
        
        print("   Embeddings ready")
        logger.info(f"Loaded embeddings: {self.embeddings.shape}")

        # NOTE: Semantic model is loaded LAZILY on first search to save memory
        # This allows the server to start with minimal RAM usage
        logger.info("✅ Data loaded. Semantic model will load on first query.")
        
        # NOTE: Cross-Encoder disabled because we have Hindi data but English Model.
        # The Multilingual Vector Model + Keyword search is much more accurate.
        self.cross_encoder = None 
        
        print("\n✅ Krishna is ready!")
        print("Semantic model will load on first question (saves memory).\n")



        # 4. Initialize Tools
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.llm_generator = LLMAnswerGenerator(api_key=self.groq_api_key)
            except Exception as e:
                logger.warning(f"Groq init failed: {e}")
    
    def _ensure_semantic_model(self):
        """Lazy load semantic model only when needed."""
        if self.semantic_model is None:
            logger.info(f"🔄 Loading Semantic Model: {settings.SENTENCE_TRANSFORMER_MODEL}")
            print("Loading AI model (first time only)...")
            self.semantic_model = TextEmbedding(model_name=settings.SENTENCE_TRANSFORMER_MODEL)
            logger.info("✅ Semantic model loaded")
            print("✅ Model ready!\n")

    def _understand_query(self, query: str) -> Dict[str, str]:
        """
        Refine the query into multiple perspectives for maximum coverage.
        Returns: { 'original': ..., 'english': ..., 'keywords': ... }
        
        OPTIMIZATION: Skip expensive LLM call for simple queries.
        """
        # Quick check: Is this a simple query that doesn't need LLM refinement?
        query_lower = query.lower()
        simple_patterns = [
            'anger', 'peace', 'fear', 'karma', 'dharma', 'life', 'death',
            'क्रोध', 'शांति', 'भय', 'कर्म', 'धर्म', 'जीवन', 'मृत्यु',
            'love', 'hate', 'work', 'duty', 'meditation',
            'प्रेम', 'घृणा', 'काम', 'कर्तव्य', 'ध्यान'
        ]
        
        # If query is short and contains common keywords, skip LLM
        word_count = len(query.split())
        has_simple_keyword = any(pattern in query_lower for pattern in simple_patterns)
        
        if word_count <= 8 and has_simple_keyword:
            # Simple query - skip LLM, use direct mapping
            logger.info(f"⚡ Simple query detected, skipping LLM refinement")
            return {
                'original': query,
                'english': query,
                'keywords': query
            }
        
        # OPTIMIZATION: Skip expensive LLM refinement for ALL queries to meet <2s latency goal.
        # The hybrid search (FastEmbed + Keywords) is robust enough.
        logger.info(f"⚡ Skipping LLM refinement for speed")
        return {
            'original': query,
            'english': query,
            'keywords': query
        }

        # Legacy LLM refinement code (Commented out for speed)
        # if not self.groq_client: 
        #     return {'original': query, 'english': query, 'keywords': query}
            
        # try:
        #     prompt = ... (omitted) ...
        #     # resp = self.groq_client.chat.completions.create(...)
        #     # result = json.loads(resp.choices[0].message.content)
        #     # return result
            
        # except Exception as e:
        #     return {'original': query, 'english': query, 'keywords': query}

    def _keyword_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Enhanced keyword search with:
        1. Modern Context Mapping (Job, Suicide, Exam -> Specific Shlokas)
        2. Narrative Filtering (Penalize Sanjay/Dhritarashtra verses)
        3. Comprehensive Keyword Matching
        """
        query_lower = query.lower()
        scores = {}
        
        # 1. MODERN CONTEXT MAPPING (The "Bridge")
        # Map modern problems directly to the BEST philosophical shlokas
        modern_mappings = {
            # CRISIS / SUICIDE -> Soul Eternity, Do not yield, Divine Protection
            'suicide': ['2.20', '2.22', '2.3', '18.66', '2.11'],
            'die': ['2.20', '2.22', '2.3', '18.66', '2.13', '2.27'],
            'kill myself': ['2.20', '2.22', '18.66'],
            'hopeless': ['18.66', '9.22', '4.11', '18.78'],
            
            # WORK / CAREER / FAILURE -> Duty (2.47), Equanimity (2.38, 2.14)
            'job': ['2.47', '2.48', '3.8', '18.47', '18.48'],
            'work': ['2.47', '3.8', '3.19', '18.45', '18.46'],
            'exam': ['2.47', '2.38', '2.14', '6.5'],
            'fail': ['2.47', '2.38', '2.14', '6.5', '2.50'],
            'result': ['2.47', '2.55', '18.11', '5.10'],
            'money': ['2.47', '18.38', '17.20', '16.13'],
            
            # RELATIONSHIPS / EMOTIONS -> Attachment (2.62-63), Peace (2.71)
            'breakup': ['2.62', '2.63', '2.66', '5.22', '18.54'],
            'love': ['2.62', '2.63', '12.13', '12.14'],
            'lonely': ['6.30', '9.29', '18.54', '13.16'],
            'cheat': ['3.37', '16.21', '16.23'],
            
            # MENTAL HEALTH -> Mind Control (6.6, 6.35), Meditation
            'depression': ['2.3', '6.5', '6.6', '18.35'],
            'anxiety': ['2.14', '6.26', '6.35', '18.66'],
            'stress': ['2.14', '2.56', '2.71', '12.15'],
            'confused': ['2.7', '18.61', '18.66', '18.73'],
            'anger': ['2.63', '16.21', '3.37', '3.38']
        }

        # Check for modern triggers
        boosted_shlokas = set()
        for term, ids in modern_mappings.items():
            if term in query_lower:
                for sid in ids:
                    boosted_shlokas.add(sid)
                    
        # 2. DEFINITIVE KEYWORD MAPPING
        keywords = {
            # Core concepts
            'anger': ['krodh', 'gussa', 'krud', 'anger', 'rage', 'wrath', 'क्रोध', 'गुस्सा'],
            'peace': ['shanti', 'calm', 'peace', 'शांति', 'शान्ति', 'sukh', 'सुख'],
            'fear': ['bhaya', 'dar', 'fear', 'afraid', 'भय', 'डर'],
            'action': ['karma', 'action', 'work', 'कर्म', 'कार्य', 'कर्तव्य'],
            'duty': ['dharma', 'duty', 'धर्म', 'कर्तव्य', 'kartavya'],
            'knowledge': ['gyan', 'jnana', 'knowledge', 'ज्ञान', 'vidya', 'विद्या'],
            'devotion': ['bhakti', 'love', 'devotion', 'भक्ति', 'प्रेम', 'prem'],
            
            # Life & Purpose
            'life': ['jeevan', 'life', 'जीवन', 'जीना', 'jeena', 'living', 'जिंदगी', 'zindagi'],
            'path': ['marg', 'path', 'way', 'मार्ग', 'राह', 'raah', 'रास्ता', 'raasta'],
            'purpose': ['uddeshya', 'purpose', 'goal', 'lakshya', 'उद्देश्य', 'लक्ष्य', 'aim'],
            'truth': ['satya', 'truth', 'सत्य', 'sach', 'सच'],
            
            # Mental states
            'mind': ['man', 'manas', 'mind', 'मन', 'मनस', 'buddhi', 'बुद्धि'],
            'desire': ['kama', 'iccha', 'desire', 'काम', 'इच्छा', 'wish', 'vasana', 'वासना'],
            'attachment': ['moha', 'asakti', 'attachment', 'मोह', 'आसक्ति', 'mamta', 'ममता'],
            'ego': ['ahamkar', 'ego', 'अहंकार', 'pride', 'ghamand', 'घमंड'],
            
            # Spiritual concepts
            'self': ['atma', 'atman', 'self', 'soul', 'आत्मा', 'स्व'],
            'god': ['ishwar', 'bhagwan', 'god', 'ईश्वर', 'भगवान', 'परमात्मा', 'paramatma'],
            'yoga': ['yoga', 'योग', 'yog', 'union', 'sadhana', 'साधना'],
            'meditation': ['dhyan', 'meditation', 'ध्यान', 'समाधि', 'samadhi'],
            
            # Emotions & Qualities
            'happiness': ['sukh', 'anand', 'happiness', 'joy', 'सुख', 'आनंद', 'खुशी', 'khushi'],
            'sorrow': ['dukh', 'sorrow', 'pain', 'दुःख', 'दुख', 'grief', 'shok', 'शोक'],
            'wisdom': ['vivek', 'pragya', 'wisdom', 'विवेक', 'प्रज्ञा', 'buddhi', 'बुद्धि'],
            'balance': ['samata', 'balance', 'समता', 'संतुलन', 'santulan', 'equanimity'],
            
            # Actions & Results
            'result': ['phal', 'result', 'फल', 'outcome', 'parinaam', 'परिणाम'],
            'renunciation': ['tyag', 'sannyasa', 'renunciation', 'त्याग', 'संन्यास'],
            'sacrifice': ['yagya', 'sacrifice', 'यज्ञ', 'havan', 'हवन'],
            
            # Relationships
            'family': ['parivar', 'family', 'परिवार', 'relatives', 'संबंधी', 'sambandhi'],
            'friend': ['mitra', 'friend', 'मित्र', 'dost', 'दोस्त', 'सखा', 'sakha'],
            'enemy': ['shatru', 'enemy', 'शत्रु', 'dushman', 'दुश्मन']
        }
        
        scores = {}
        for idx, item in enumerate(self.shlokas):
            txt = item['searchable_text']
            verse_id = item.get('id', '')
            score = 0.0
            
            # 3. DIRECT BOOSTING for modern contexts
            # If shloka ID is in the boosted list for this query, give huge boost
            if verse_id in boosted_shlokas:
                score += 15.0  # Massive score boost for manually curated matches
            
            # 4. NARRATIVE FILTER (Penalize non-Krishna speakers for advice queries)
            # If verse is likely narrative (Sanjay/Dhritarashtra speaking), reduce score
            # We want "Sri Bhagavan Uvacha" (God said) or meaningful questions
            sanskrit_start = item.get('sanskrit', '').strip().lower()
            narrator_markers = ['सञ्जय उवाच', 'अर्जुन उवाच', 'धृतराष्ट्र उवाच', 'sanjaya uvacha', 'arjuna uvacha', 'dhritarashtra uvacha']
            
            is_narrative = any(marker in sanskrit_start for marker in narrator_markers)
            if is_narrative:
                # But don't penalize if it's a boosted shloka (sometimes Arjuna's question is relevant context)
                if verse_id not in boosted_shlokas:
                    score -= 5.0  # Penalty for narrative verses

            # Count keyword matches
            matched_categories = 0
            for key, terms in keywords.items():
                query_has_term = any(t in query_lower for t in terms)
                shloka_has_term = any(t in txt for t in terms)
                
                if query_has_term and shloka_has_term:
                    score += 2.5  # Strong boost for keyword match
                    matched_categories += 1
            
            # Bonus for multiple category matches (indicates high relevance)
            if matched_categories >= 2:
                score += matched_categories * 1.0
                        
            if score > 0:
                scores[idx] = score
                
        # Sort by score
        sorted_indices = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_indices[:top_k]

    def _semantic_search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """Deep semantic vector search."""
        if self.embeddings is None:
            return []
        
        # Lazy load model on first use
        self._ensure_semantic_model()
        
        if not self.semantic_model:
            return []
             
        # FastEmbed returns a generator of batches, so we list() it to get all batches
        # Since we only send one query, we get one batch, take the first item
        # The result is a numpy array of embeddings
        embedding_gen = self.semantic_model.embed([query])
        # Force list conversion to inspect
        try:
            batches = list(embedding_gen)
            if not batches or len(batches[0]) == 0:
                logger.error("FastEmbed returned no embeddings")
                return []
            
            q_vec = batches[0][0]
            
            # Ensure q_vec is 2D (1, dim) for sklearn
            if hasattr(q_vec, 'reshape'):
                q_vec = q_vec.reshape(1, -1)
            else:
                q_vec = np.array([q_vec])

            # Ensure embeddings is 2D (N, dim)
            # If embeddings is 1D (flattened), means N*dim elements.
            # We need to reshape it to (-1, dim)
            if hasattr(self.embeddings, 'ndim') and self.embeddings.ndim == 1:
                # If embeddings got flattened, reshape it back? Or assume it's one sample?
                if self.embeddings.shape[0] > 0:
                     # Calculate assuming standard dimension
                     # FastEmbed (bge-small-en-v1.5) dim = 384
                     dim = 384
                     if self.embeddings.shape[0] % dim == 0:
                         logger.warning(f"Embeddings array is 1D: {self.embeddings.shape}. Reshaping to (-1, {dim}).")
                         self.embeddings = self.embeddings.reshape(-1, dim)
                     else:
                         # Fallback or error?
                         logger.error(f"Embeddings 1D shape {self.embeddings.shape} not divisible by {dim}. Cannot reshape.")
                         return []

            if len(self.embeddings) == 0:
                 return []

            sims = cosine_similarity(q_vec, self.embeddings)[0]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
        # Get indices
        idxs = np.argsort(sims)[::-1][:top_k]
        return [(int(i), float(sims[i])) for i in idxs]

    def search(self, query: str, method: str = "hybrid", top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Multi-Perspective Search Strategy to find the 'Sahi Shloka'.
        """
        self._load_resources()
        
        # 1. Continuous Refining (Get multiple angles)
        variations = self._understand_query(query)
        
        candidates = {} # Map id -> score
        
        # 2. Search from English Perspective (Semantic Vectors work best here)
        eng_res = self._semantic_search(variations.get('english', query), top_k=75)
        for idx, score in eng_res:
            candidates[idx] = candidates.get(idx, 0.0) + score
            
        # 3. Search from Keyword Perspective (Catch specific Sanskrit terms)
        kw_query = f"{variations.get('keywords', '')} {query}"
        kw_res = self._keyword_search(kw_query, top_k=50) # Keep strong keywords
        for idx, score in kw_res:
             # Boost keyword matches significantly
            candidates[idx] = candidates.get(idx, 0.0) + (score * 1.5)
            
        # 4. Search Original (Context)
        orig_res = self._semantic_search(query, top_k=75)
        for idx, score in orig_res:
            candidates[idx] = candidates.get(idx, 0.0) + score

        # Sort and take top pool for Re-ranking
        # We INCREASED this from 40 to 100 to ensure we don't miss "hidden gems"
        pool_idxs = sorted(candidates.keys(), key=lambda k: candidates[k], reverse=True)[:100]
        
        # 5. Cross-Encoder Re-ranking (The Final Judge)
        final_idxs = pool_idxs
        if self.cross_encoder:
            # We re-rank against the ORIGINAL query + English Intent for best context matching
            rerank_query = f"{query} {variations.get('english', '')}"
            pairs = [(rerank_query, self.shlokas[i]['meaning']) for i in pool_idxs]
            
            ce_scores = self.cross_encoder.predict(pairs)
            
            # Zip and sort
            reranked = sorted(
                zip(pool_idxs, ce_scores), 
                key=lambda x: x[1], 
                reverse=True
            )
            final_idxs = [x[0] for x in reranked]
            
        # 6. Format Results
        results = []
        for i in final_idxs[:top_k]:
            item = self.shlokas[i].copy()
            results.append(item)
            
        logger.info(f"Returning {len(results)} matches after refinement.")
        return results

    def _is_greeting(self, query: str) -> bool:
        """Check if the query is a simple greeting."""
        # Comprehensive list of greetings in multiple languages
        greetings = {
            # English greetings
            "hi", "hello", "hey", "hii", "hiii", "helo", "heyy", "heya", "yo",
            "greetings", "good morning", "good afternoon", "good evening", "good night",
            "gm", "ge", "gn", "ga", "morning", "evening", "afternoon",
            
            # Hindi/Sanskrit greetings (Romanized)
            "namaste", "namaskar", "namaskaram", "pranam", "pranaam", "pranaams",
            "radhe radhe", "radhey radhey", "radhe", "radhey",
            "jai shri krishna", "jai shree krishna", "jai sri krishna", 
            "hare krishna", "hare krsna", "krishna", "krsna",
            "jai", "jay", "om", "aum",
            
            # Hindi Devanagari Script Greetings
            "हेलो", "हेल्लो", "हाय", "हाई", "हलो",
            "नमस्ते", "नमस्कार", "नमस्कारम", "प्रणाम", "प्रनाम",
            "राधे राधे", "राधे", "राधेय राधेय",
            "जय श्री कृष्ण", "जय श्रीकृष्ण", "जय कृष्ण",
            "हरे कृष्ण", "हरे कृष्णा", "कृष्ण",
            "जय", "ओम", "ॐ",
            "सुप्रभात", "शुभ संध्या", "शुभ रात्रि",
            "कैसे हो", "कैसे हैं", "क्या हाल", "क्या हाल है",
            
            # Casual/Informal
            "sup", "wassup", "whatsup", "howdy", "hola",
            "kaise ho", "kaise hain", "kya haal", "kya hal", "namaskaar"
        }
        
        # Normalize: remove only punctuation, preserve all letters (including Devanagari)
        # Keep alphanumeric + spaces + Devanagari combining marks
        import unicodedata
        cleaned = ''.join(c for c in query.lower() if c.isalnum() or c.isspace() or unicodedata.category(c).startswith('M'))
        words = cleaned.split()
        
        if not words:
            return False
        
        # Check if entire query is a greeting phrase (like "good morning")
        full_query = ' '.join(words)
        if full_query in greetings:
            return True
        
        # Check for two-word greeting phrases
        if len(words) >= 2:
            two_word = f"{words[0]} {words[1]}"
            if two_word in greetings:
                # If it's just the greeting or greeting + name, it's a greeting
                if len(words) <= 3:
                    return True
                # If longer, check for question words
                question_words = {'what', 'how', 'why', 'who', 'when', 'where', 
                                'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                                'explain', 'tell', 'batao', 'bataiye', 'btao'}
                if not any(qw in words for qw in question_words):
                    return True
        
        # STRICT CHECK: Very short queries (1-3 words) - just needs ONE greeting word
        if len(words) <= 3:
            return any(w in greetings for w in words)
        
        # MODERATE CHECK: Slightly longer (4-6 words) - must START with greeting
        # and NOT contain question words
        if len(words) <= 6:
            if words[0] in greetings:
                question_words = {'what', 'how', 'why', 'who', 'when', 'where', 
                                'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                                'explain', 'tell', 'batao', 'bataiye', 'btao',
                                'is', 'are', 'can', 'should', 'would', 'could'}
                # If no question words found, it's likely just a greeting
                if not any(qw in words for qw in question_words):
                    return True
        
        return False

    def _is_relevant_to_krishna(self, query: str) -> Tuple[bool, str]:
        """
        Check if the query is relevant to Krishna, Bhagavad Gita, or spiritual life guidance.
        Returns: (is_relevant: bool, rejection_message: str if not relevant)
        
        This prevents the model from answering out-of-context questions like:
        - Sports (cricket, football, etc.)
        - Politics (current affairs, politicians)
        - General trivia (celebrities, movies, etc.)
        - Science facts unrelated to spirituality
        """
        query_lower = query.lower()
        
        # IRRELEVANT TOPICS - These should be rejected
        irrelevant_patterns = {
            # Sports & Games
            'sports': ['cricket', 'football', 'soccer', 'match', 'ipl', 'world cup', 'player', 
                      'team', 'score', 'goal', 'wicket', 'stadium', 'olympics', 'tennis',
                      'ind vs', 'india vs', 'pakistan vs', 'match update', 'live score'],
            
            # Politics & Current Affairs
            'politics': ['election', 'minister', 'president', 'prime minister', 'parliament',
                        'government', 'party', 'vote', 'donald trump', 'biden', 'modi',
                        'congress', 'bjp', 'political', 'democracy'],
            
            # Entertainment & Celebrity
            'entertainment': ['movie', 'film', 'actor', 'actress', 'bollywood', 'hollywood',
                            'tv show', 'series', 'netflix', 'celebrity', 'singer', 'song'],
            
            # Technology & Products
            'technology': ['iphone', 'android', 'laptop', 'computer', 'software', 'app',
                         'facebook', 'instagram', 'twitter', 'whatsapp', 'google',
                         'microsoft', 'apple inc', 'samsung'],
            
            # General Trivia
            'trivia': ['capital of', 'largest', 'smallest', 'tallest', 'fastest',
                      'population', 'currency', 'flag', 'who invented', 'when was',
                      'historical event', 'world war', 'discovery'],
            
            # Science (unless spiritual)
            'science': ['chemical formula', 'periodic table', 'molecule', 'bacteria',
                       'virus covid', 'vaccine', 'dna', 'atom', 'neutron', 'electron'],
            
            # Food & Cooking (unless related to prasad/spiritual)
            'food': ['recipe for', 'how to cook', 'ingredients for', 'restaurant',
                    'pizza', 'burger', 'pasta', 'italian food'],
            
            # Weather & Geography (factual)
            'geography': ['weather today', 'temperature', 'forecast', 'rain tomorrow',
                         'climate in', 'map of', 'distance between']
        }
        
        # Check for irrelevant patterns
        for category, patterns in irrelevant_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    logger.warning(f"❌ Irrelevant query detected ({category}): '{query}'")
                    return False, f"""क्षमा करें, मैं श्री कृष्ण हूँ और केवल जीवन की समस्याओं, आध्यात्मिकता, और भगवद गीता के ज्ञान के बारे में मार्गदर्शन दे सकता हूँ।

आप मुझसे पूछ सकते हैं:
• जीवन की समस्याओं का समाधान (क्रोध, डर, चिंता, etc.)
• कर्म, धर्म, और आत्मा के बारे में
• रिश्तों और भावनाओं के बारे में
• ध्यान, शांति, और आत्म-विकास के बारे में

कृपया इन विषयों पर प्रश्न पूछें। 🙏"""
        
        # RELEVANT KEYWORDS - These indicate the query is likely relevant
        relevant_keywords = [
            # Krishna & Deities
            'krishna', 'कृष्ण', 'भगवान', 'bhagwan', 'god', 'ishwar', 'ईश्वर',
            'arjun', 'अर्जुन', 'radha', 'राधा', 'vishnu', 'विष्णु',
            
            # Bhagavad Gita & Scriptures
            'gita', 'गीता', 'shloka', 'श्लोक', 'verse', 'chapter', 'अध्याय',
            'scripture', 'sacred', 'holy', 'divine',
            
            # Spiritual Concepts
            'dharma', 'धर्म', 'karma', 'कर्म', 'yoga', 'योग', 'bhakti', 'भक्ति',
            'atma', 'आत्मा', 'soul', 'spiritual', 'आध्यात्मिक', 'meditation', 'ध्यान',
            'moksha', 'मोक्ष', 'liberation', 'enlightenment', 'nirvana', 'samadhi',
            
            # Life Guidance Topics
            'life', 'जीवन', 'purpose', 'meaning', 'path', 'मार्ग', 'way',
            'problem', 'समस्या', 'solution', 'समाधान', 'help', 'मदद', 'guide',
            
            # Emotions & Mental States (Valid spiritual topics)
            'anger', 'क्रोध', 'peace', 'शांति', 'fear', 'भय', 'anxiety', 'चिंता',
            'stress', 'depression', 'sad', 'दुख', 'happy', 'सुख', 'joy', 'आनंद',
            'confused', 'असमंजस', 'lost', 'hopeless', 'निराश',
            
            # Relationships (Valid spiritual topics)
            'love', 'प्रेम', 'hate', 'घृणा', 'family', 'परिवार', 'friend', 'मित्र',
            'relationship', 'संबंध', 'marriage', 'विवाह', 'breakup',
            
            # Work & Duty (Valid spiritual topics)
            'work', 'काम', 'job', 'नौकरी', 'duty', 'कर्तव्य', 'responsibility',
            'success', 'सफलता', 'failure', 'असफलता', 'exam', 'परीक्षा',
            
            # Existential Questions (Valid)
            'why', 'क्यों', 'how', 'कैसे', 'what is', 'क्या है', 'who am i',
            'death', 'मृत्यु', 'birth', 'जन्म', 'suffering', 'कष्ट',
            'desire', 'इच्छा', 'attachment', 'मोह', 'ego', 'अहंकार'
        ]
        
        # If query contains any relevant keyword, it's likely valid
        if any(keyword in query_lower for keyword in relevant_keywords):
            logger.info(f"✅ Relevant query detected: '{query}'")
            return True, ""
        
        # If query is a general life question without specific irrelevant keywords
        # we allow it (benefit of doubt for spiritual guidance)
        general_question_words = ['why', 'how', 'what', 'when', 'should i', 'can i',
                                 'kya', 'kaise', 'kab', 'kyun', 'क्या', 'कैसे']
        
        if any(qw in query_lower for qw in general_question_words):
            # It's a question, and we didn't find irrelevant patterns
            # Let's allow it as it might be seeking life guidance
            logger.info(f"✅ General life question allowed: '{query}'")
            return True, ""
        
        # If we reach here, the query is likely too vague or unrelated
        logger.warning(f"⚠️ Unclear query relevance: '{query}'")
        return False, f"""क्षमा करें, मैं आपके प्रश्न को पूरी तरह से समझ नहीं पाया। मैं श्री कृष्ण हूँ और जीवन की समस्याओं का समाधान देने के लिए यहाँ हूँ।

आप मुझसे पूछ सकते हैं:
• जीवन की चुनौतियों का सामना कैसे करें?
• क्रोध, भय, या चिंता से कैसे मुक्त हों?
• कर्म, धर्म, और जीवन के उद्देश्य के बारे में
• रिश्तों और भावनाओं के बारे में मार्गदर्शन

कृपया अपना प्रश्न स्पष्ट रूप से पूछें। 🙏"""

    def search_with_llm(self, query: str, conversation_history: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """End-to-end RAG answer with conversation context."""
        
        # 0. Check for Greeting
        if self._is_greeting(query):
             return {
                 "answer": "राधे राधे! मैं श्री कृष्ण हूँ। कहिये, मैं आपकी क्या सहायता कर सकता हूँ?",
                 "shlokas": [],
                 "llm_used": True
             }

        # 0.5 Check if query is relevant to Krishna/Bhagavad Gita context
        is_relevant, rejection_message = self._is_relevant_to_krishna(query)
        if not is_relevant:
            logger.warning(f"Rejecting irrelevant query: '{query}'")
            return {
                "answer": rejection_message,
                "shlokas": [],
                "llm_used": False,
                "rejected": True  # Flag to indicate query was rejected
            }

        # 1. Retrieve - Increased to 5 to give LLM better options
        shlokas = self.search(query, top_k=5)
        
        # Log retrieved shlokas for debugging
        logger.info(f"📖 Retrieved {len(shlokas)} shlokas for query: '{query}'")
        for i, s in enumerate(shlokas, 1):
            logger.info(f"  {i}. Gita {s['id']}: {s['meaning'][:80]}...")
        
        # 2. Generate with conversation context
        if not self.llm_generator:
             return {"answer": "LLM not connected.", "shlokas": shlokas, "llm_used": False}
             
        return self.llm_generator.generate_answer(query, shlokas, conversation_history=conversation_history or [])

    # Legacy wrappers for compatibility
    def _get_llm_generator(self):
        """Backwards compatibility for CLI."""
        if not self.llm_generator:
            self.llm_generator = LLMAnswerGenerator(api_key=self.groq_api_key)
        return self.llm_generator

    def format_results(self, results: List[Dict[str, Any]], query: str, method: str) -> str:
        """Format results for display (fallback mode)."""
        output = [f"\nSearch Results for: '{query}'", "-" * 70]
        for i, res in enumerate(results, 1):
             meaning = res.get('meaning', 'No meaning available')[:200].replace('\n', ' ')
             output.append(f"{i}. Gita {res['id']}")
             output.append(f"   {meaning}...")
             output.append("")
        return "\n".join(output)
